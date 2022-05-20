import asyncio
import dataclasses
import functools
import gzip
import pathlib
from typing import ClassVar, Dict, List, Optional, Tuple, Union

import aiohttp
import injector
from loguru import logger
import orjson

from labbie import constants
from labbie import errors
from labbie import state
from labbie import utils

_Constants = constants.Constants
_LOADERS = {}


def loader(type_):
    def decorator(fn):
        _LOADERS[type_] = fn
        return fn
    return decorator


@loader('.json.gz')
def load_json_gz(path: pathlib.Path):
    with gzip.open(path) as f:
        content = f.read().decode('utf8')
    return orjson.loads(content)


@loader('.json')
def load_json(path: pathlib.Path):
    with path.open(encoding='utf8') as f:
        return orjson.loads(f.read())


def get_loader(path: pathlib.Path):
    suffixes = path.suffixes

    for i in range(len(suffixes)):
        type_ = ''.join(suffixes[i:])
        if loader := _LOADERS.get(type_):
            return loader

    raise ValueError(f'No loader specified for file with suffixes {suffixes}')


@dataclasses.dataclass
class Resource:
    _CONTAINER_URL: ClassVar[str] = 'https://labbie.blob.core.windows.net/resources'

    version: int
    path_format: str

    @functools.cached_property
    def path(self) -> pathlib.Path:
        return pathlib.Path(self.path_format.format(version=self.version))

    @functools.cached_property
    def url(self) -> pathlib.Path:
        return f'{self._CONTAINER_URL}/{self.path}'

    @functools.cached_property
    def name(self) -> pathlib.Path:
        return self.path.name

    def local_path(self, resources_dir: pathlib.Path):
        return resources_dir / self.name

    def cached_hash_path(self, resources_dir: pathlib.Path):
        local_path = self.local_path(resources_dir)
        return local_path.parent / f'{local_path.name}.md5'

    async def needs_update(self, resources_dir: pathlib.Path,
                           session: Optional[aiohttp.ClientSession] = None):
        async with utils.client_session(session) as session:
            async with session.head(self.url) as resp:
                if resp.status == 404:
                    return True
                cached_hash = self.cached_hash(resources_dir)
                remote_hash = resp.headers['Content-MD5']
                needs_update = cached_hash != remote_hash
                logger.debug(f'{self.local_path(resources_dir)} {needs_update=} '
                             f'{cached_hash=}{"==" if not needs_update else "!="}{remote_hash=}')
                return needs_update

    def cached_hash(self, resources_dir: pathlib.Path):
        hash_path = self.cached_hash_path(resources_dir)

        if not hash_path.exists():
            return None

        with hash_path.open(encoding='utf8') as f:
            return f.read()

    async def load_or_download(self, resources_dir: pathlib.Path, force: bool = False,
                               session: Optional[aiohttp.ClientSession] = None):
        needs_update = await self.needs_update(resources_dir, session=session)
        if force or needs_update:
            async with utils.client_session(session) as session:
                async with session.get(self.url) as resp:
                    if resp.status != 200:
                        raise errors.FailedToDownloadResource(self.url)

                    content = await resp.content.read()
                    hash = resp.headers['Content-MD5']
                    self.save(resources_dir, content, hash)

        return self.load(resources_dir)

    def save(self, resources_dir: pathlib.Path, content: Union[str, bytes], hash: str):
        kwargs = {}
        if isinstance(content, str):
            mode = 'w'
            kwargs['encoding'] = 'utf8'
        elif isinstance(content, bytes):
            mode = 'wb'
        else:
            raise ValueError(f'Invalid content type, expected str or bytes but got {type(content).__name__}')

        local_path = self.local_path(resources_dir)
        with local_path.open(mode, **kwargs) as f:
            f.write(content)

        hash_path = self.cached_hash_path(resources_dir)
        with hash_path.open('w', encoding='utf8') as f:
            f.write(hash)

    def load(self, resources_dir: pathlib.Path):
        local_path = self.local_path(resources_dir)
        loader = get_loader(local_path)
        return loader(local_path)


@injector.singleton
class ResourceManager:

    # NOTE: file names must not collide, as the local path only includes the name and not the full path
    _RESOURCES = {
        'trade_stats': Resource(version=3, path_format='pathofexile/{version}/stats.json.gz'),
        'items': Resource(version=3, path_format='pathofexile/{version}/items.json.gz'),
        'mods': Resource(version=3, path_format='repoe/{version}/mods.json.gz'),
    }

    @injector.inject
    def __init__(self, constants: _Constants, app_state: state.AppState):
        self._constants = constants
        self._app_state = app_state

        self._init_task = None

        # NOTE: the following attributes are set by _get_all_resources
        self.trade_stats: Dict[str, str] = None
        self.items: Dict[str, List[Tuple[bool, str, str]]] = None
        self.mods: Dict[str, List[List[str, List[str], List[Union[float, int, str]], bool]]] = None

    def initialize(self):
        self._constants.resources_dir.mkdir(parents=True, exist_ok=True)
        self._init_task = asyncio.create_task(self._get_all_resources())

    async def _get_all_resources(self):
        # TODO(bnorick): handle potential PermissionError / OSError from disk write failures in a reasonable way
        async with aiohttp.ClientSession() as session:
            for name, resource in self._RESOURCES.items():
                value = await resource.load_or_download(
                    resources_dir=self._constants.resources_dir, session=session)
                setattr(self, name, value)
        self._app_state.resources_ready = True
