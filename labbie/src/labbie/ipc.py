import sys
from multiprocessing import shared_memory
import time

import loguru

from labbie import version

logger = loguru.logger

_SHARED_LIST = None
_DEFAULT_ENTRIES = [1] + list(version.VERSION_NUMBER) + [False]
# 7 values:
#    0 -> (int) instance count
#    1 -> (int) major version of running instance
#    2 -> (int) minor version of running instance
#    3 -> (int) patch version of running instance
#    4 -> (int) prerelease type
#           none  = 1000 (so that 0.8.0 > 0.8.0-rc.1)
#           alpha = 0
#           beta  = 1
#           rc    = 2
#    5 -> (int) prerelease version
#    6 -> (bool) exit signal
#           stay alive = False
#           exit = True
_INSTANCES_INDEX = 0
_VERSION_START_INDEX = 1
_VERSION_END_INDEX = 5
_EXIT_SIGNAL_INDEX = 6


def get_shm():
    global _SHARED_LIST

    if _SHARED_LIST is not None:
        return _SHARED_LIST

    logger.info('Initializing IPC shared memory')
    try:
        _SHARED_LIST = shared_memory.ShareableList(_DEFAULT_ENTRIES)
    except FileExistsError:
        _SHARED_LIST = shared_memory.ShareableList(name='labbie_ipc')

    return _SHARED_LIST


def close_shm():
    if _SHARED_LIST is not None:
        _SHARED_LIST.shm.close()


def initialize(force=False):
    if is_running():
        running_version = get_running_version()
        if running_version < version.VERSION_NUMBER or force:
            logger.info(f'Labbie v{version.from_tuple(running_version)} is already running, communicating '
                        f'that it should exit.')
            signal_exit()
            while should_exit():
                time.sleep(0.05)
        else:
            signal_foreground()
            logger.info(f'Labbie v{version.from_tuple(running_version)} is already running.')
            logger.info('Exiting')
            sys.exit()


def is_running():
    shm = get_shm()
    return shm[_INSTANCES_INDEX] > 0


def get_running_version():
    shm = get_shm()
    return tuple(shm[_VERSION_START_INDEX:_VERSION_END_INDEX + 1])


def signal_exit():
    shm = get_shm()
    shm[_EXIT_SIGNAL_INDEX] = True


def signal_foreground():
    shm = get_shm()
    shm[_INSTANCES_INDEX] += 1


def should_exit():
    shm = get_shm()
    return shm[_EXIT_SIGNAL_INDEX]


def should_foreground():
    shm = get_shm()
    return shm[_INSTANCES_INDEX] > 1


def foregrounded():
    shm = get_shm()
    shm[_INSTANCES_INDEX] = 1
