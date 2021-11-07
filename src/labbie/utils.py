import atexit
import mmap
import os
import pathlib
import sys

import loguru

logger = loguru.logger


def root_dir():
    if getattr(sys, 'frozen', False):
        # The application is frozen
        return pathlib.Path(sys.executable).parent
    else:
        # The application is not frozen
        return pathlib.Path(__file__).parent.parent.parent


def logs_dir():
    return root_dir() / 'logs'


def assets_dir():
    return root_dir() / 'assets'


def bin_dir():
    return root_dir() / 'bin'


def default_config_dir():
    return root_dir() / 'config'


def default_data_dir():
    return root_dir() / 'data'


def relaunch(debug, exit_fn=None):
    cmd = []
    if sys.argv[0] == 'labbie':
        from labbie import __main__ as main
        cmd.append(main.__file__)
    else:
        cmd.append(f'"{sys.argv[0]}"')
    if debug:
        cmd.append('--debug')
    if not getattr(sys, 'frozen', False):
        cmd.insert(0, f'"{sys.executable}"')

    logger.info(f'{sys.argv=}')
    logger.info(f'{cmd=}')
    atexit.register(os.execv, sys.executable, cmd)
    if exit_fn:
        exit_fn()
    else:
        sys.exit(0)


def instances_shm():
    return mmap.mmap(-1, 1, 'labbie_instances')


def exit_if_already_running():
    mm = instances_shm()
    if mm[0] > 0:
        mm[0] += 1
        logger.info(f'Labbie is already running, instances={mm[0]}')
        sys.exit()


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
