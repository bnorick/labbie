import asyncio
import atexit
import functools
import os
import pathlib
import subprocess
import sys
from typing import Optional, Union

import loguru

from updater import paths

logger = loguru.logger
_FROZEN = getattr(sys, 'frozen', False)


def root_dir():
    if is_frozen():
        # root/bin/updater/Updater.exe
        return pathlib.Path(sys.executable).parent.parent.parent.resolve()
    else:
        # When running from python, not frozen, we consider the build directory to be the root
        # repo/updater/src/updater/utils.py
        # repo/package/build/Labbie (root)
        repo_dir = pathlib.Path(__file__).parent.parent.parent.parent
        return (repo_dir / 'package' / 'build' / 'Labbie').resolve()


def updater_dir():
    if is_frozen():
        # .../updater/Updater.exe
        return pathlib.Path(sys.executable).parent.resolve()
    else:
        # .../updater/src/updater/utils.py
        return pathlib.Path(__file__).parent.parent.parent.resolve()


def assets_dir():
    return updater_dir() / 'assets'


def built_labbie_dir():
    return root_dir() / 'bin' / 'labbie'


def built_updater_dir():
    return root_dir() / 'bin' / 'updater'


def update_path():
    sys.path.append(str(built_labbie_dir() / 'lib'))
    if is_frozen():
        sys.path.append(str(root_dir() / 'lib'))


def freeze_others():
    from labbie import utils as labbie_utils
    labbie_utils._FROZEN = True


def is_frozen():
    return _FROZEN


def get_paths(data_dir: pathlib.Path = None):
    return paths.Paths(root=root_dir(), data=data_dir)


def resolve_path(path: Union[str, pathlib.Path]):
    return pathlib.Path(path).resolve()


def set_skipped_version(version: str, paths: Optional[paths.Paths] = None):
    if paths is None:
        paths = get_paths()
    logger.debug(paths.updater_data / 'skip.txt')
    with (paths.updater_data / 'skip.txt').open('w', encoding='utf8') as f:
        f.write(version)


def should_skip_version(version: str, paths: Optional[paths.Paths] = None):
    if paths is None:
        paths = get_paths()

    skip_path = (paths.updater_data / 'skip.txt')
    if not skip_path.exists():
        return False

    with skip_path.open('r', encoding='utf8') as f:
        skipped = f.read().rstrip()

    return skipped == version


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
    delayed_move = (f'"ping 192.0.2.1 -n 1 -w {int(delay * 1000)} '
                    f'& move "{path_from.resolve()}" "{path_to.resolve()}""')
    command = f'cmd /s /c {delayed_move}'
    logger.info(f'Renaming later: {path_from=} {path_to=} {command=}')
    subprocess.Popen(command, stdout=subprocess.DEVNULL, shell=True)


def fix_taskbar_icon():
    import ctypes
    myappid = 'updater.id'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def exit_and_launch_labbie(exit_fn=None):
    executable = str(built_labbie_dir() / 'Labbie.exe')
    cmd = [executable]
    logger.info(f'{cmd=}')
    atexit.register(os.execv, executable, cmd)
    if exit_fn:
        exit_fn()
    else:
        sys.exit(0)


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
