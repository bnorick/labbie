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


def assets_dir():
    return root_dir() / 'assets'


def bin_dir():
    return root_dir() / 'bin'


def default_config_dir():
    return root_dir() / 'config'


def default_data_dir():
    return root_dir() / 'data'


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
