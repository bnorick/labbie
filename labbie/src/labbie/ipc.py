import asyncio
import sys
from multiprocessing import shared_memory
import time

import loguru

from labbie import version

logger = loguru.logger

_SHARED_LIST = None
_DEFAULT_ENTRIES = [0] + list(version.VERSION.version_tuple) + [False]
_CREATED_SHM = False
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
    global _SHARED_LIST, _CREATED_SHM

    if _SHARED_LIST is not None:
        return _SHARED_LIST

    logger.info('Initializing IPC shared memory')
    try:
        logger.info('Creating IPC shared memory')
        _CREATED_SHM = True
        _SHARED_LIST = shared_memory.ShareableList(_DEFAULT_ENTRIES, name='labbie_ipc')
    except FileExistsError:
        _SHARED_LIST = shared_memory.ShareableList(name='labbie_ipc')

    return _SHARED_LIST


def close_shm():
    if _SHARED_LIST is not None:
        _SHARED_LIST.shm.close()


def initialize(force=False):
    if is_running():
        running_version = get_running_version()
        if running_version < version.VERSION.version_tuple or force:
            logger.info(f'Labbie v{version.VERSION.str_from_tuple(running_version)} is already running, communicating '
                        f'that it should exit.')
            signal_exit()
            wait_for_exit()
            set_running_version()
        else:
            signal_foreground()
            logger.info(f'Labbie v{version.VERSION.str_from_tuple(running_version)} is already running.')
            logger.info('Exiting')
            sys.exit()
    else:
        mark_running()


def mark_running():
    shm = get_shm()
    shm[_INSTANCES_INDEX] += 1


def is_running():
    shm = get_shm()
    return shm[_INSTANCES_INDEX] > 0


def get_running_version():
    shm = get_shm()
    version = []
    for index in range(_VERSION_START_INDEX, _VERSION_END_INDEX + 1):
        version.append(shm[index])
    return tuple(version)


def set_running_version():
    shm = get_shm()
    for index, val in enumerate(version.VERSION.version_tuple, start=_VERSION_START_INDEX):
        shm[index] = val


def signal_exit():
    shm = get_shm()
    shm[_EXIT_SIGNAL_INDEX] = True


def should_exit():
    shm = get_shm()
    return shm[_EXIT_SIGNAL_INDEX]


def exited():
    shm = get_shm()
    shm[_EXIT_SIGNAL_INDEX] = False


def signal_foreground():
    shm = get_shm()
    shm[_INSTANCES_INDEX] += 1


def should_foreground():
    shm = get_shm()
    return shm[_INSTANCES_INDEX] > 1


def foregrounded():
    shm = get_shm()
    shm[_INSTANCES_INDEX] = 1


def wait_for_exit():
    while should_exit():
        time.sleep(0.05)


async def wait_for_exit_async():
    while should_exit():
        await asyncio.sleep(0.05)
