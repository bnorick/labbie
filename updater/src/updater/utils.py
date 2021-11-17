import pathlib
import subprocess
import sys

import loguru

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


def repository_path():
    if getattr(sys, 'frozen', False):
        return root_dir() / 'bin' / 'updater' / 'repo'
    else:
        return root_dir() / 'updater' / 'repo'


def get_labbie_version():
    if getattr(sys, 'frozen', False):
        # The application is frozen
        version = subprocess.check_output([str(root_dir() / 'bin' / 'labbie' / 'Labbie.exe'), '--version'])
    else:
        version = subprocess.check_output([sys.executable, '-m', 'labbie', '--version'])
    return version.decode('utf8')


def rename_later(path_from, path_to, delay):
    command = [
        'cmd',
        '/c',
        f'ping 192.0.2.1 -n 1 -w {int(delay * 1000)} & move "{path_from.resolve()}" "{path_to.resolve()}"'
    ]
    subprocess.Popen(command, stdout=subprocess.DEVNULL)
