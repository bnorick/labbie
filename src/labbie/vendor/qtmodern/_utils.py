import sys
import platform
from os.path import join, dirname, abspath

from PyQt5.QtCore import QT_VERSION_STR

QT_VERSION = tuple(int(v) for v in QT_VERSION_STR.split('.'))
""" tuple: Qt version. """

PLATFORM = platform.system()


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return join(sys._MEIPASS, dirname(abspath(__file__)), relative_path)
    return join(dirname(abspath(__file__)), relative_path)
