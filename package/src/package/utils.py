import pathlib


def root_dir():
    # root/package/src/package/utils.py
    return pathlib.Path(__file__).parent.parent.parent.parent


def labbie_dir():
    return root_dir() / 'labbie'


def updater_dir():
    return root_dir() / 'updater'


def build_dir():
    return root_dir() / 'package' / 'build'
