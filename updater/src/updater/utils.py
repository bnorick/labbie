import asyncio
import functools
import os
import pathlib
import subprocess
import sys
from typing import Union

import loguru

from updater import paths

logger = loguru.logger


def root_dir():
    if getattr(sys, 'frozen', False):
        # The application is frozen
        # root/bin/updater/Updater.exe
        return pathlib.Path(sys.executable).parent.parent.parent
    else:
        # The application is not frozen
        # root/updater/src/updater/utils.py
        return pathlib.Path(__file__).parent.parent.parent.parent


def updater_dir():
    if getattr(sys, 'frozen', False):
        # The application is frozen
        # .../updater/Updater.exe
        return pathlib.Path(sys.executable).parent
    else:
        # The application is not frozen
        # .../updater/src/updater/utils.py
        return pathlib.Path(__file__).parent.parent.parent


def assets_dir():
    return updater_dir() / 'assets'


def update_path():
    if getattr(sys, 'frozen', False):
        sys.path.append(str(root_dir() / 'bin' / 'labbie' / 'lib'))
        sys.path.append(str(root_dir() / 'lib'))


def get_paths(data_dir: pathlib.Path = None):
    return paths.Paths(root=root_dir(), data=data_dir)


def resolve_path(path: Union[str, pathlib.Path]):
    return pathlib.Path(path).resolve()


def get_labbie_version():
    labbie_dir = root_dir() / 'bin' / 'labbie'
    if not (labbie_dir / 'Labbie.com').exists():
        raise RuntimeError(f'Missing labbie build at {labbie_dir}')
    env = os.environ.copy()
    env['QT_API'] = 'pyqt5'
    version = subprocess.check_output([str(labbie_dir / 'Labbie.com'), '--version'], env=env, shell=True)
    return version.decode('utf8').strip()


def rename_later(path_from, path_to, delay):
    command = [
        'cmd',
        '/c',
        f'ping 192.0.2.1 -n 1 -w {int(delay * 1000)} & move "{path_from.resolve()}" "{path_to.resolve()}"'
    ]
    subprocess.Popen(command, stdout=subprocess.DEVNULL)


def fix_taskbar_icon():
    import ctypes
    myappid = 'updater.id'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


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
