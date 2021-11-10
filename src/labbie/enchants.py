import asyncio
import collections
import dataclasses
import datetime
import enum
import functools
import gzip
import io
import pathlib
import re
from typing import List, NamedTuple, Optional, Set, Dict
from base64 import b64decode

import aiohttp
import loguru
import orjson
from github import Github

from labbie import constants
from labbie import errors
from labbie import mixins

logger = loguru.logger
_FILENAME_FORMAT = '{date:%Y-%m-%d}.json.gz'
_URL_FORMAT = f'https://labbie.blob.core.windows.net/enchants/{{type}}/{_FILENAME_FORMAT}'
_MOD_URL_FORMAT = f'https://labbie.blob.core.windows.net/mods.json.gz'
_VALUE_PATTERN = re.compile(r'-?\d*\.?\d+')
_HISTORICAL_DAYS = 15
_REFRESH_DELAY = 5 * 60  # 5 minutes
_Constants = constants.Constants


class Helm(NamedTuple):

    item_name: str
    item_base: Optional[str]
    ilvl: Optional[int]
    influences: List[str]
    unique: bool


@dataclasses.dataclass
class Enchant:

    account: str
    character: str
    item_name: str
    item_base: str
    display_name: str = dataclasses.field(init=False, default=None)
    ilvl: int
    influences: List[str]
    unique: bool
    mods: List[str]

    def __post_init__(self):
        self.display_name = self.item_name if self.unique else self.item_base

    def matches_helm(self, target: Helm):
        if target.unique:
            if self.item_name != target.item_name:
                return False
        else:
            if self.item_base != target.item_base:
                return False

        if self.ilvl < target.ilvl:
            return False

        for influence in target.influences:
            if influence not in self.influences:
                return False

        return True


class State(enum.Enum):

    DISABLED = 'Disabled via settings'
    DOWNLOADING = 'Downloading latest'
    LOADING = 'Loading'
    LOADED = 'Loaded'
    MISSING = 'Missing enchant data'


@dataclasses.dataclass
class Enchants(mixins.ObservableMixin):

    type: str
    state: State = State.DISABLED
    enchants: Optional[List[Enchant]] = None
    date: Optional[datetime.date] = None

    def __post_init__(self):
        super().__init__()
        self._refresh_task = None

    def set_enchants(self, date: Optional[datetime.date], enchants: Optional[List[Enchant]]):
        if enchants is not None:
            self.state = State.LOADED
        else:
            self.state = State.DISABLED
            if self._refresh_task:
                self._refresh_task.cancel()
                self._refresh_task = None
        self.enchants = enchants
        self.date = date
        self.notify(enchants=enchants, date=date, _log=False)

    # def load(self, path):
    #     # TODO: make this async
    #     try:
    #         date, enchants_ = load_enchants(path)
    #         self.date = date
    #         self.set_enchants(date, enchants_)
    #     except errors.EnchantDataNotFound:
    #         self.state = State.MISSING
    #         raise

    def refresh_needed(self):
        return self.date != datetime.date.today()

    async def download_or_load(self, constants: _Constants):
        logger.info(f'starting refresh task for {self.type}')
        self._refresh_task = asyncio.create_task(self._download_when_available(constants))

        cache_dir = constants.helm_enchants_dir / self.type
        today = today_utc()

        # first try to load from cache if most recent data is cached
        try:
            self.state = State.LOADING
            date, enchants = load_enchants(cache_dir, date=today)
            self.set_enchants(date, enchants)
            return
        except errors.EnchantDataNotFound:
            pass

        # either most recent data cache was corrupt or we don't have it, load most recent cached if it's
        # the most recent downloadable, otherwise download latest
        first_cached, last_cached = cached_dates(cache_dir)
        last_downloadable = await last_downloadable_date(constants.user_agent, self.type, past_days=_HISTORICAL_DAYS)

        # try to load (fresh) cached content if we can
        if last_cached is not None:
            date = last_cached
            earliest_date = first_cached if last_downloadable is None else last_downloadable
            while date >= earliest_date:
                try:
                    self.state = State.LOADING
                    date, enchants = load_enchants(cache_dir, date=date)
                    self.set_enchants(date, enchants)
                    return
                except errors.EnchantDataInvalid:
                    date -= datetime.timedelta(days=1)
                except errors.EnchantDataNotFound:
                    # ignore missing files
                    break

        if last_downloadable is None:
            self.state = State.MISSING
            return

        try:
            self.state = State.DOWNLOADING
            date, enchants = await download(cache_dir, self.type, constants.user_agent,
                                            past_days=_HISTORICAL_DAYS)
            self.set_enchants(date, enchants)
        except errors.EnchantDataNotFound:
            # this shouldn't happen because we checked the last downloadable date and one existed within
            # _HISTORICAL_DAYS
            logger.debug(f'{first_cached=} {last_cached=} {last_downloadable=}')
            raise

    async def _download_when_available(self, constants: _Constants):
        await asyncio.sleep(15)
        cache_dir = constants.helm_enchants_dir / self.type
        while True:
            if self.date == today_utc():
                now = datetime.datetime.now(datetime.timezone.utc)
                tomorrow = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
                duration = (tomorrow - now).total_seconds()
                logger.info(f'{self.type} scrape is fresh, sleeping until tomorrow ({duration=})')
                await asyncio.sleep(duration)

            while True:
                logger.info(f'checking if fresh {self.type} scrape is downloadable')
                available = await last_downloadable_date(constants.user_agent, self.type, 1)
                if available:
                    self.state = State.DOWNLOADING
                    date, enchants = await download(cache_dir, self.type, constants.user_agent,
                                                    past_days=_HISTORICAL_DAYS)
                    self.set_enchants(date, enchants)
                    break
                else:
                    await asyncio.sleep(_REFRESH_DELAY)

    @property
    def enabled(self):
        return self.state is not State.DISABLED

    @property
    def bases(self):
        if self.state is not State.LOADED:
            raise errors.EnchantsNotLoaded

        return set(enchant.display_name for enchant in self.enchants)

    @property
    def mods(self):
        if self.state is not State.LOADED:
            raise errors.EnchantsNotLoaded

        mods = set()
        for enchant in self.enchants:
            mods.update(set(enchant.mods))

        return mods

    def find_matching_enchants(self, target: str):
        if self.state is not State.LOADED:
            raise errors.EnchantsNotLoaded
        return find_matching_enchants(self.enchants, target)

    def find_matching_helms(self, target: Helm):
        if self.state is not State.LOADED:
            raise errors.EnchantsNotLoaded
        return find_matching_helms(self.enchants, target)

    def find_matching_bases(self, base_name: str, ilvl: int, influences: List[str]):
        logger.debug(f'{influences=}')
        if self.state is not State.LOADED:
            raise errors.EnchantsNotLoaded

        for enchant in self.enchants:
            if enchant.display_name == base_name:
                unique = enchant.unique
                item_name = enchant.item_name
                item_base = enchant.item_base
                break
        else:
            raise errors.NoSuchBase
        helm = Helm(item_name=item_name, item_base=item_base, ilvl=ilvl, influences=influences, unique=unique)
        return find_matching_helms(self.enchants, helm)


def today_utc():
    return datetime.datetime.now(datetime.timezone.utc).date()


def refresh_needed(cache_dir: pathlib.Path):
    path = cache_dir / _FILENAME_FORMAT.format(date=today_utc())
    return not path.exists()


def cached_dates(cache_dir: pathlib.Path):
    paths = sorted(cache_dir.iterdir())

    earliest_date = None
    for path in paths:
        try:
            earliest_date = datetime.date.fromisoformat(path.stem)
            break
        except ValueError:
            pass
    else:
        # short circuit if we found no valid date filenames
        return None, None

    latest_date = None
    for path in reversed(paths):
        try:
            latest_date = datetime.date.fromisoformat(path.stem)
            break
        except ValueError:
            pass

    return earliest_date, latest_date


async def last_downloadable_date(user_agent: str, type_: str, past_days):
    today = today_utc()
    async with aiohttp.ClientSession(headers={'User-Agent': user_agent}) as session:
        for days_back in range(past_days):
            date = today - datetime.timedelta(days=days_back)
            async with session.head(_URL_FORMAT.format(type=type_, date=date)) as resp:
                if resp.status == 404:
                    continue

                return date
    return None

async def download(cache_dir: pathlib.Path, type_: str, user_agent: str, past_days: int):
    logger.info(f'downloading {type_} enchants')
    today = today_utc()
    async with aiohttp.ClientSession(headers={'User-Agent': user_agent}) as session:
        for days_back in range(past_days):
            date = today - datetime.timedelta(days=days_back)
            async with session.get(_URL_FORMAT.format(type=type_, date=date)) as resp:
                if resp.status == 404:
                    continue

                logger.info(f'found data for {date=:%Y-%m-%d}')
                content = await resp.content.read()
                path = cache_dir / _FILENAME_FORMAT.format(date=date)
                with path.open('wb') as f:
                    f.write(content)
                with gzip.open(io.BytesIO(content)) as f:
                    decompressed_content = f.read()
                try:
                    enchants = [Enchant(*vals) for vals in orjson.loads(decompressed_content)]
                except orjson.JSONDecodeError:
                    logger.error(f'Invalid enchant data downloaded for {date=}')
                    path.unlink()
                    continue
                return date, enchants

        logger.error(f'no data found for the last {past_days} days, aborting')
        # if nothing was found for the window, raise
        raise errors.EnchantDataNotFound


async def last_mod_update_date(user_agent: str):
    async with aiohttp.ClientSession(headers={'User-Agent': user_agent}) as session:
        async with session.head(_MOD_URL_FORMAT) as resp:
                if resp.status == 404:
                    pass
                return 
    return None

async def download_mod_data(cache_dir: pathlib.Path, user_agent: str):
    path = cache_dir / 'mods.json.gz'
    async with aiohttp.ClientSession(headers={'User-Agent': user_agent}) as session:
        async with session.get(_MOD_URL_FORMAT) as resp:
                if resp.status == 404:
                    pass

                content = await resp.content.read()
                with path.open('wb') as f:
                    f.write(content)
                with gzip.open(io.BytesIO(content)) as f:
                    decompressed_content = f.read()
                mods = orjson.loads(decompressed_content)

                return mods


def load_enchants(cache_dir: pathlib.Path, date=None):
    if date is not None:
        dates = (date, )
    else:
        today = today_utc()
        dates = (today - datetime.timedelta(days=days_back) for days_back in range(15))

    for date in dates:
        path = cache_dir / _FILENAME_FORMAT.format(date=date)
        if path.exists():
            try:
                with gzip.open(path) as f:
                    content = f.read().decode('utf8')
                return date, [Enchant(*vals) for vals in orjson.loads(content)]
            except orjson.JSONDecodeError:
                # delete broken files when we find them
                path.unlink()

    raise errors.EnchantDataNotFound


def find_matching_enchants(enchants: List[Enchant], target: str):
    target = target.lower()
    logger.info(f'{target=}')
    matches = []
    for enchant in enchants:
        for mod in enchant.mods:
            if target in mod.lower() or target in unexact_mod(mod).lower():
                matches.append(enchant)
    return matches


def find_matching_helms(enchants: List[Enchant], target: Helm):
    matches = []
    for enchant in enchants:
        if enchant.matches_helm(target):
            matches.append(enchant)
    return matches


def unexact_mod(mod):
    return _VALUE_PATTERN.sub('#', mod)

def enchant_summary(enchants: List[Enchant]):
    items = collections.Counter()
    influences = collections.defaultdict(collections.Counter)
    ilvls = collections.defaultdict(list)
    rare_bases = []

    for enchant in enchants:
        items[enchant.display_name] += 1
        if not enchant.unique:
            influences[enchant.item_base][', '.join(enchant.influences) or 'None'] += 1
            ilvls[enchant.item_base].append(enchant.ilvl)
            rare_bases.append(enchant.item_base)

    summary = []

    summary.append('Bases')
    summary.extend(f'  {count:>3d} {val}' for val, count in items.most_common())

    if rare_bases:
        rare_bases = [val for val, _ in items.most_common() if val in rare_bases]

        summary.append('')
        for base in rare_bases:
            summary.append(f'{base} ({items[base]})')
            summary.append('  Influence')
            summary.extend(f'    {count:>3d} {val}' for val, count in influences[base].most_common())

            summary.append('')
            summary.append('  Item Level')
            item_levels = sorted(ilvls[base], reverse=True)
            last = item_levels[0]
            appended = False
            count = 0
            for count, ilvl in enumerate(item_levels[1:], start=1):
                if ilvl == last:
                    continue

                prefix = '>=' if appended else '  '
                summary.append(f'    {count:>3d} {prefix}{last:>3d}')
                appended = True
                last = ilvl

            count += 1
            prefix = '>=' if appended else '  '
            summary.append(f'    {count:>3d} {prefix}{last:>3d}')
            summary.append('')
    return '\n'.join(summary)


def base_summary(enchants: List[Enchant]):
    mods = collections.Counter()

    for enchant in enchants:
        for mod in enchant.mods:
            mods[unexact_mod(mod)] += 1

    summary = [f'  {count:>3d} {val}' for val, count in mods.most_common()]

    return '\n'.join(summary)

@dataclasses.dataclass
class Mods(mixins.ObservableMixin):

    state: State = State.DISABLED
    mods: Optional[Set[str]] = None

    def get_mod_list_from_partial(self, enchant_list):
        full_enchants = []
        potential_enchants = []
        for partial_enchant in enchant_list:
            if partial_enchant == '':
                continue
            partial_enchant = unexact_mod(partial_enchant.lower().replace('’', "'"))
            logger.debug(f'{partial_enchant=}')
            # continuation of enchant
            if potential_enchants:
                is_partial_enchant = False
                for enchant in potential_enchants:
                    if partial_enchant in enchant:
                        logger.debug(f'partial part of previous {partial_enchant=}')
                        if enchant not in full_enchants:
                            full_enchants.append(enchant)
                        is_partial_enchant = True
                if is_partial_enchant:
                    continue
                # odd scenario where there are multiple potential enchants but no follow up lines to determine wich is correct
                # main scenario this happens is with plurals
                if len(potential_enchants) > 1:
                    full_enchants.append(potential_enchants[0])
            potential_enchants = []
            for mod in self.mods:
                if mod.startswith(partial_enchant):
                    potential_enchants.append(mod)
                    logger.debug(f'Mod found! {partial_enchant=}----{mod=}')

            if len(potential_enchants) == 1:
                full_enchants.append(potential_enchants[0])
        # odd scenario where there are multiple potential enchants but no follow up lines to determine wich is correct
        # main scenario this happens is with plurals
        if len(potential_enchants) > 1:
            full_enchants.append(potential_enchants[0])
        logger.info(f'found {full_enchants=}')
        return full_enchants

    async def download_or_load(self, constants):
        cache_dir = constants.mod_dir
        # first try to load from cache if most recent data is cached
        try:
            logger.info('Loading enchant mod data')
            self.state = State.LOADING
            mods = None
            if check_file_changed():
               mods = load_mods(cache_dir)
            else:
                self.state = State.DOWNLOADING
                mods = await self.download_mods(cache_dir)
            
        except errors.ModDataNotFound:
            self.state = State.DOWNLOADING
            mods = await self.download_mods(cache_dir)
        self.state.LOADED
        self.mods = set(mods)
        
    async def download_mods(self, path: pathlib.Path):
        logger.info('Downloading new mod data')
        file_SHAs = {}
        file_contents = {}
        for file in self.repoe_content_files:
            file_SHAs[file.name] = file.sha
            blob = self.repoe_repo.get_git_blob(file.sha)
            file_contents[file.name] = orjson.loads(b64decode(blob.content))

        mod_ids = []
        for mod in file_contents['mods.json'].values():
            if "Enchantment" in mod['group']:
                for stat in mod['stats']:
                    mod_ids.append(stat['id'])
        
        mod_strings = []

        for stat in file_contents['stat_translations.json']:
            id_found = False
            for id_ in stat['ids']:
                if id_ in mod_ids:
                    id_found = True
                    break
            if not id_found:
                continue

            for x in stat['English']:
                mod_strings.append(unexact_mod(x['string'].format(*x['format']).lower()))

        with gzip.open(path / 'mods.json.gz', 'wb') as f:
            f.write(orjson.dumps(mod_strings))

        with (path / 'file_SHAs.json').open('wb') as f:
            f.write(orjson.dumps(file_SHAs))
        return mod_strings


def load_SHAs(path: pathlib.Path):
    path /= 'file_SHAs.json'
    if path.exists():
        try:
            with path.open(encoding='utf-8') as f:
                content = f.read()
                file_SHAs = orjson.loads(content)
            return file_SHAs
        except orjson.JSONDecodeError:
            # delete broken files when we find them
            path.unlink()
    raise errors.ModDataNotFound

def load_mods(path: pathlib.Path):
    path /= 'mods.json.gz'
    if path.exists():
        try:
            with gzip.open(path) as f:
                content = f.read().decode('utf8')
                mods = orjson.loads(content)
            return mods
        except orjson.JSONDecodeError:
            # delete broken files when we find them
            path.unlink()
    
    raise errors.ModDataNotFound