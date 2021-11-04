import collections
import dataclasses
import datetime
import enum
import pathlib
import re
from typing import List, NamedTuple, Optional

import aiohttp
import loguru
import orjson

from labbie import errors
from labbie import mixins

logger = loguru.logger
_FILENAME_FORMAT = '{date:%Y-%m-%d}.json'
_URL_FORMAT = f'https://labbie.blob.core.windows.net/enchants/{{type}}/{_FILENAME_FORMAT}'
_VALUE_PATTERN = re.compile(r'\d+')
_UNSET = object()


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

    DOWNLOADING = 'Downloading latest'
    LOADING = 'Loading'
    LOADED = 'Loaded'
    MISSING = 'Missing enchant data'


@dataclasses.dataclass
class Enchants(mixins.ObservableMixin):

    type: str
    state: State = State.LOADING
    enchants: Optional[List[Enchant]] = None
    date: Optional[datetime.date] = None

    def __post_init__(self):
        super().__init__()

    def update_enchants(self, date: Optional[datetime.date], enchants: Optional[List[Enchant]]):
        if enchants:
            self.state = State.LOADED
        else:
            self.state = State.MISSING
        self.enchants = enchants
        self.date = date
        self.notify(enchants=enchants)

    def load(self, path):
        # TODO: make this async
        try:
            date, enchants_ = load_enchants(path)
            self.date = date
            self.update_enchants(date, enchants_)
        except errors.EnchantDataNotFound:
            self.state = State.MISSING
            raise

    def refresh_needed(self):
        return self.date != datetime.date.today()

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


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def refresh_needed(cache_dir: pathlib.Path):
    path = cache_dir / _FILENAME_FORMAT.format(date=now())
    return not path.exists()


async def download(cache_dir: pathlib.Path, curr_enchants: Enchants, user_agent: str):
    logger.debug(f'downloading {curr_enchants.type} enchants')
    today = now()
    async with aiohttp.ClientSession(headers={'User-Agent': user_agent}) as session:
        for days_back in range(15):
            date = today - datetime.timedelta(days=days_back)
            async with session.get(_URL_FORMAT.format(type=curr_enchants.type, date=date)) as resp:
                if resp.status == 404:
                    continue

                if curr_enchants.date and curr_enchants.date >= date:
                    raise errors.EnchantDataNotFound

                curr_enchants.state = State.DOWNLOADING
                content = await resp.text(encoding='utf8')
                with (cache_dir / _FILENAME_FORMAT.format(date=date)).open('w', encoding='utf8') as f:
                    f.write(content)

                curr_enchants.state = State.LOADING
                enchants = [Enchant(*vals) for vals in orjson.loads(content)]

                logger.debug(f'setting enchants for {curr_enchants.type}')
                curr_enchants.update_enchants(date, enchants)

                break
        else:
            raise errors.EnchantDataNotFound


def load_enchants(cache_dir: pathlib.Path):
    today = now()
    for days_back in range(15):
        date = today - datetime.timedelta(days=days_back)
        path = cache_dir / _FILENAME_FORMAT.format(date=date)
        if path.exists():
            with path.open(encoding='utf8') as f:
                content = f.read()
                return date, [Enchant(*vals) for vals in orjson.loads(content)]
    raise errors.EnchantDataNotFound


def find_matching_enchants(enchants: List[Enchant], target: str):
    target = target.lower()
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
