import sys
import platform
from os.path import join, dirname, abspath

from qtpy import QtCore

QT_VERSION = tuple(int(v) for v in QtCore.__version__.split('.'))
""" tuple: Qt version. """

PLATFORM = platform.system()


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return join(sys._MEIPASS, dirname(abspath(__file__)), relative_path)
    return join(dirname(abspath(__file__)), relative_path)
