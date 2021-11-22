import asyncio
import atexit
import contextlib
import dataclasses
import functools
import os
import pathlib
import shutil
import sys
from typing import Literal, Optional

import loguru

from labbie import version

logger = loguru.logger

_FROZEN = getattr(sys, 'frozen', False)


def is_frozen():
    return _FROZEN


@contextlib.contextmanager
def temporary_freeze():
    global _FROZEN
    orig = _FROZEN
    try:
        _FROZEN = True
        yield
    finally:
        _FROZEN = orig


# The following function is based on one available in aiofiles and is liscensed under the Apache2 license
# see https://github.com/Tinche/aiofiles/blob/master/src/aiofiles/os.py (source)
# and https://github.com/Tinche/aiofiles/blob/master/LICENSE (license)
# modifications:
#     minor edits to conform to Google Style Guide
def wrap(func):
    @functools.wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def root_dir():
    if is_frozen():
        # The application is frozen
        # .../root/bin/labbie/Labbie.exe
        return pathlib.Path(sys.executable).parent.parent.parent
    else:
        # The application is not frozen
        # .../root/labbie/src/labbie/utils.py
        return pathlib.Path(__file__).parent.parent.parent.parent


def labbie_dir():
    if is_frozen():
        # The application is frozen
        # .../labbie/Labbie.exe
        return pathlib.Path(sys.executable).parent
    else:
        # The application is not frozen
        # .../labbie/src/labbie/utils.py
        return pathlib.Path(__file__).parent.parent.parent


def logs_dir():
    return root_dir() / 'logs'


def assets_dir():
    return labbie_dir() / 'assets'


def bin_dir():
    return root_dir() / 'bin'


def default_config_dir():
    default = root_dir() / 'config'
    if not is_frozen() and not default.exists():
        shutil.copytree(labbie_dir() / 'config', default)
    return default


def default_data_dir():
    return root_dir() / 'data'


def update_path():
    if is_frozen():
        sys.path.append(str(root_dir() / 'lib'))
        sys.path.append(str(root_dir() / 'bin' / 'updater' / 'lib'))
    else:
        import subprocess
        version_bytes = subprocess.check_output(['poetry', 'env', 'info', '--path'],
                                                cwd=str(root_dir() / 'updater')).rstrip()
        updater_env_path = pathlib.Path(version_bytes.decode('utf8'))
        sys.path.append(str(updater_env_path / 'Lib' / 'site-packages'))
        sys.path.append(str(root_dir() / 'updater' / 'src'))


def relaunch(debug, exit_fn=None):
    cmd = []
    if sys.argv[0] == 'labbie':
        from labbie import __main__ as main
        cmd.append(main.__file__)
    else:
        cmd.append(f'"{sys.argv[0]}"')
    if debug:
        cmd.append('--debug')
    if not is_frozen():
        cmd.insert(0, f'"{sys.executable}"')

    logger.info(f'{sys.argv=}')
    logger.info(f'{cmd=}')
    atexit.register(os.execv, sys.executable, cmd)
    if exit_fn:
        exit_fn()
    else:
        sys.exit(0)


def exit_and_launch_updater(prereleases, exit_fn=None):
    if not is_frozen():
        os.chdir(root_dir() / 'updater')
        executable = 'poetry'
        cmd = ['run', 'updater']
    else:
        executable = str(root_dir() / 'bin' / 'updater' / 'Updater.exe')
        cmd = []

    if prereleases:
        cmd.append('--prerelease')

    logger.info(f'{cmd=}')
    atexit.register(os.execv, executable, cmd)
    if exit_fn:
        exit_fn()
    else:
        sys.exit(0)


def _check_for_update(release_type: Literal['release', 'prerelease']) -> Optional[str]:
    from updater import components
    from updater import utils
    component = components.COMPONENTS['labbie']
    component.load()

    latest = component.latest_version(release_type)
    if latest is None:
        return None
    elif latest > version.__version__ and not utils.should_skip_version(str(latest)):
        return str(latest)
    elif not latest.is_prerelease() and component.version.is_prerelease():
        return str(latest)
    return None


check_for_update = wrap(_check_for_update)


def make_slotted_dataclass(cls):
    # Need to create a new class, since we can't set __slots__
    #  after a class has been created.

    # Make sure __slots__ isn't already set.
    if '__slots__' in cls.__dict__:
        raise TypeError(f'{cls.__name__} already specifies __slots__')

    # Create a new dict for our new class.
    cls_dict = dict(cls.__dict__)
    field_names = tuple(f.name for f in dataclasses.fields(cls))
    cls_dict['__slots__'] = field_names
    for field_name in field_names:
        # Remove our attributes, if present. They'll still be
        #  available in _MARKER.
        cls_dict.pop(field_name, None)
    # Remove __dict__ itself.
    cls_dict.pop('__dict__', None)
    # And finally create the class.
    qualname = getattr(cls, '__qualname__', None)
    cls = type(cls)(cls.__name__, cls.__bases__, cls_dict)
    if qualname is not None:
        cls.__qualname__ = qualname
    return cls


class LogFilter:

    def __init__(self, level):
        self.level = level

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, val):
        self._level = logger.level(val).no

    def __call__(self, record):
        return record['level'].no >= self.level
