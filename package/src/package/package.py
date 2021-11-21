import multiprocessing
import shutil

import cx_Freeze
import setuptools
import typer

from package import utils

app = typer.Typer()


def package_labbie():
    from labbie import version

    labbie_dir = utils.labbie_dir()
    labbie_build_dir = utils.labbie_build_dir()

    package_dir = {'': str(labbie_dir / 'src')}
    packages = setuptools.find_packages(str(labbie_dir / 'src'))
    package_data = {'': ['*'], 'labbie': ['vendor/qtmodern/resources/*']}

    executables = [
        cx_Freeze.Executable(
            str(labbie_dir / 'entry_point.py'),
            base='Win32GUI',
            target_name='Labbie.exe',
            icon=str(labbie_dir / 'assets' / 'icon.ico')
        ),
        cx_Freeze.Executable(
            str(labbie_dir / 'entry_point.py'),
            base=None,
            target_name='Labbie.com'
        )
    ]

    setup_kwargs = {
        'name': 'Labbie',
        'version': '.'.join(str(v) for i, v in enumerate(version.to_tuple(version.__version__)) if i != 3),
        'author': 'Brandon Norick',
        'author_email': 'b.norick@gmail.com',
        'package_dir': package_dir,
        'packages': packages,
        'package_data': package_data,
        'options': {
            'build_exe': {
                'build_exe': str(labbie_build_dir),
                'excludes': ['tkinter', 'test'],
                'include_files': [str(labbie_dir / 'assets'), str(labbie_dir / 'LICENSE')]
            }
        },
        'executables': executables,
        'script_name': 'setup.py',
        'script_args': ['build']
    }

    cx_Freeze.setup(**setup_kwargs)

    for path in labbie_build_dir.rglob('Labbie.com.exe'):
        path.rename(path.with_suffix(''))

    for path in labbie_build_dir.rglob('python38.dll'):
        if path.parent != labbie_build_dir:
            path.unlink()


def package_updater():
    from updater import version

    updater_dir = utils.updater_dir()
    updater_build_dir = utils.updater_build_dir()

    package_dir = {'': str(updater_dir / 'src')}
    packages = setuptools.find_packages(str(updater_dir / 'src'))
    package_data = {'': ['*'], 'updater': ['vendor/qtmodern/resources/*']}

    executables = [
        cx_Freeze.Executable(
            str(updater_dir / 'entry_point.py'),
            base='Win32GUI',
            target_name='Updater.exe',
            icon=str(updater_dir / 'assets' / 'icon.ico')
        ),
        cx_Freeze.Executable(
            str(updater_dir / 'entry_point.py'),
            base=None,
            target_name='Updater.com'
        )
    ]

    setup_kwargs = {
        'name': 'Updater',
        'version': version.__version__,
        'author': 'Brandon Norick',
        'author_email': 'b.norick@gmail.com',
        'package_dir': package_dir,
        'packages': packages,
        'package_data': package_data,
        'options': {
            'build_exe': {
                'build_exe': str(updater_build_dir),
                'excludes': ['tkinter', 'test', 'labbie', 'PySide2'],
                'include_files': [
                    str(updater_dir / 'repo'),
                    str(updater_dir / 'assets'),
                    str(updater_dir / 'LICENSE')
                ]
            }
        },
        'executables': executables,
        'script_name': 'setup.py',
        'script_args': ['build']
    }

    cx_Freeze.setup(**setup_kwargs)

    for path in updater_build_dir.rglob('Updater.com.exe'):
        path.rename(path.with_suffix(''))

    for path in updater_build_dir.rglob('python38.dll'):
        if path.parent != updater_build_dir:
            path.unlink()


@app.command()
def package():
    labbie_proc = multiprocessing.Process(target=package_labbie)
    updater_proc = multiprocessing.Process(target=package_updater)

    labbie_proc.start()
    updater_proc.start()

    labbie_proc.join()
    updater_proc.join()

    root_dir = utils.root_dir()
    build_dir = utils.build_dir() / 'Labbie'
    lib_dir = build_dir / 'lib'

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    lib_dir.mkdir()

    labbie_build_dir = utils.labbie_build_dir()
    updater_build_dir = utils.updater_build_dir()
    tesseract_dir = root_dir / 'bin' / 'tesseract'

    shutil.copytree(labbie_build_dir, build_dir / 'bin' / 'labbie', dirs_exist_ok=True)
    shutil.copytree(updater_build_dir, build_dir / 'bin' / 'updater', dirs_exist_ok=True)
    shutil.copytree(tesseract_dir, build_dir / 'bin' / 'tesseract', dirs_exist_ok=True)
    shutil.move(str(build_dir / 'bin' / 'labbie' / 'lib' / 'PySide2'), build_dir / 'lib')
    shutil.move(str(build_dir / 'bin' / 'labbie' / 'lib' / 'shiboken2'), build_dir / 'lib')
    shutil.copy(root_dir / 'README.md', build_dir / 'README.md')
    shutil.copytree(root_dir / 'config', build_dir / 'config', dirs_exist_ok=True)
