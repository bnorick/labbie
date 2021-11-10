import asyncio
import gzip
import pathlib
from typing import Dict, List, Optional, Tuple, Union

import aiohttp
import injector
from loguru import logger
import orjson

from labbie import constants
from labbie import errors
from labbie import state
from labbie import utils

_Constants = constants.Constants
_PathLike = Union[str, pathlib.Path]
_CONTAINER_URL = 'https://labbie.blob.core.windows.net/enchants'
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


@injector.singleton
class ResourceManager:

    @injector.inject
    def __init__(self, constants: _Constants, app_state: state.AppState):
        self._constants = constants
        self._app_state = app_state
        self.trade_stats: Dict[str, str] = None
        self.items: Dict[str, List[Tuple[bool, str, str]]] = None
        self.mods: Dict[str, Dict[str, List[List[Union[str, int]]]]] = None
        self._init_task = None

    def initialize(self):
        self._constants.resources_dir.mkdir(parents=True, exist_ok=True)
        self._init_task = asyncio.create_task(self._get_all_resources())

    async def _get_all_resources(self):
        # TODO(bnorick): handle PermissionError / OSError from disk write failures in a reasonable way

        async with aiohttp.ClientSession() as session:
            self.trade_stats = await self.load_or_download_resource('trade_stats.json.gz', session=session)
            self.items = await self.load_or_download_resource('trade_items.json.gz', session=session)
            self.mods = await self.load_or_download_resource('mods.json.gz', session=session)
        self._app_state.resources_ready = True

    async def resource_needs_update(self, resource_path: _PathLike, session: Optional[aiohttp.ClientSession] = None):
        async with utils.client_session(session) as session:
            async with session.head(f'{_CONTAINER_URL}/{resource_path}') as resp:
                if resp.status == 404:
                    return True
                cached_hash = self.cached_resource_hash(resource_path)
                remote_hash = resp.headers['Content-MD5']
                needs_update = cached_hash != remote_hash
                logger.debug(f'{resource_path=} {needs_update=} {cached_hash=}{"==" if not needs_update else "!="}{remote_hash=}')

                return needs_update

    def cached_resource_hash(self, resource_path: _PathLike):
        local_resource_path = self.local_resource_path(resource_path)
        hash_path = local_resource_path.parent / f'{local_resource_path.name}.md5'

        if not hash_path.exists():
            return None

        with hash_path.open(encoding='utf8') as f:
            return f.read()

    async def load_or_download_resource(self, resource_path: _PathLike, force: bool = False,
                                        session: Optional[aiohttp.ClientSession] = None):
        needs_update = await self.resource_needs_update(resource_path, session)
        if needs_update:
            async with utils.client_session(session) as session:
                remote_resource = self.remote_resource_path(resource_path)
                async with session.get(remote_resource) as resp:
                    if resp.status != 200:
                        raise errors.FailedToDownloadResource(remote_resource)

                    content = await resp.content.read()
                    hash = resp.headers['Content-MD5']
                    self.save(resource_path, content, hash)

        return self.load(resource_path)

    def save(self, resource_path: _PathLike, content: Union[str, bytes], hash: str):
        kwargs = {}
        if isinstance(content, str):
            mode = 'w'
            kwargs['encoding'] = 'utf8'
        elif isinstance(content, bytes):
            mode = 'wb'
        else:
            raise ValueError(f'Invalid content type, expected str or bytes but got {type(content).__name__}')

        local_resource_path = self.local_resource_path(resource_path)
        with local_resource_path.open(mode, **kwargs) as f:
            f.write(content)

        hash_path = local_resource_path.parent / f'{local_resource_path.name}.md5'
        with hash_path.open('w', encoding='utf8') as f:
            f.write(hash)


    def load(self, resource_path: _PathLike):
        local_resource_path = self.local_resource_path(resource_path)
        loader = get_loader(local_resource_path)
        return loader(local_resource_path)

    def remote_resource_path(self, resource_path: _PathLike):
        return f'{_CONTAINER_URL}/{resource_path}'

    def local_resource_path(self, resource_path: _PathLike):
        resource_path = pathlib.Path(resource_path)
        return self._constants.resources_dir / resource_path
