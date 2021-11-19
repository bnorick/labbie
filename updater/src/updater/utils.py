import asyncio
import functools
import pathlib
import subprocess
import sys
import tempfile
from typing import Union

import loguru

from updater import paths

logger = loguru.logger


def root_dir():
    if getattr(sys, '_really_frozen', False):
        # root/bin/updater/Updater.exe
        return pathlib.Path(sys.executable).parent.parent.parent.resolve()
    else:
        # root/updater/src/updater/utils.py
        return pathlib.Path(__file__).parent.parent.parent.parent.resolve()


def updater_dir():
    if getattr(sys, '_really_frozen', False):
        # .../updater/Updater.exe
        return pathlib.Path(sys.executable).parent.resolve()
    else:
        # .../updater/src/updater/utils.py
        return pathlib.Path(__file__).parent.parent.parent.resolve()


def assets_dir():
    return updater_dir() / 'assets'


def built_labbie_dir():
    if getattr(sys, '_really_frozen', False):
        return root_dir() / 'bin' / 'labbie'
    else:
        return root_dir() / 'package' / 'build' / 'Labbie' / 'bin' / 'labbie'


def built_updater_dir():
    if getattr(sys, '_really_frozen', False):
        return root_dir() / 'bin' / 'updater'
    else:
        return root_dir() / 'package' / 'build' / 'Labbie' / 'bin' / 'updater'


def update_path():
    sys.path.append(str(built_labbie_dir() / 'lib'))
    if getattr(sys, '_really_frozen', False):
        sys.path.append(str(root_dir() / 'lib'))


def fake_freeze():
    # Act as if we're frozen all the time, for the purposes of python code like the labbie package
    # but maintain true frozen state to use internally
    really_frozen = getattr(sys, 'frozen', False)
    sys.frozen = True
    sys._really_frozen = really_frozen


def get_paths(data_dir: pathlib.Path = None):
    return paths.Paths(root=root_dir(), data=data_dir)


def resolve_path(path: Union[str, pathlib.Path]):
    return pathlib.Path(path).resolve()


def get_labbie_version():
    # labbie_dir = built_labbie_dir()
    # if not (labbie_dir / 'Labbie.com').exists():
    #     raise RuntimeError(f'Missing labbie build at {labbie_dir}')
    # startupinfo = subprocess.STARTUPINFO()
    # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # startupinfo.wShowWindow = subprocess.SW_HIDE
    # stdout_file = tempfile.NamedTemporaryFile(mode='r+', delete=False)
    # process = subprocess.Popen(
    #     [str(labbie_dir / 'Labbie.com'), '--version'],
    #     stdin=subprocess.PIPE,
    #     stdout=stdout_file,
    #     stderr=subprocess.PIPE,
    #     shell=False,
    #     startupinfo=startupinfo
    # )
    # return_code = process.wait()
    # stdout_file.flush()
    # stdout_file.seek(0)  # This is required to reset position to the start of the file
    # version = stdout_file.read()
    # stdout_file.close()

    # return version
    from labbie import version
    return version.__version__


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
