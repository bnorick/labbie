import cx_Freeze
import setuptools


def package_labbie():
    from labbie import version
    from package import utils

    labbie_dir = utils.labbie_dir()
    labbie_build_dir = utils.build_dir() / 'labbie'

    package_dir = {'': str(labbie_dir / 'src')}
    packages = setuptools.find_packages(str(labbie_dir / 'src'))
    package_data = {'': ['*'], 'labbie': ['vendor/qtmodern/resources/*']}

    executables = [
        cx_Freeze.Executable(
            str(labbie_dir / 'entry_point.py'),
            base='Win32GUI',
            target_name='Labbie.exe',
            icon=str(labbie_dir / 'assets' / 'taxi-32.ico')
        ),
        cx_Freeze.Executable(
            str(labbie_dir / 'entry_point.py'),
            base=None,
            target_name='Labbie.com'
        )
    ]

    setup_kwargs = {
        'name': 'Labbie',
        'version': version.__version__,
        'author': 'Brandon Norick',
        'author_email': 'b.norick@gmail.com',
        'package_dir': package_dir,
        'packages': packages,
        'package_data': package_data,
        'options': {
            'build_exe': {
                'build_exe': str(labbie_build_dir),
                'include_files': [str(labbie_dir / 'assets'), str(labbie_dir / 'LICENSE')]
            }
        },
        'executables': executables,
    }

    cx_Freeze.setup(**setup_kwargs)
    for path in labbie_build_dir.rglob('Labbie.com.exe'):
        path.rename(path.with_suffix(''))


def package_updater():
    from updater import version
    from package import utils

    updater_dir = utils.updater_dir()
    updater_build_dir = utils.build_dir() / 'updater'

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
                'include_files': [str(updater_dir / 'assets'), str(updater_dir / 'LICENSE')]
            }
        },
        'executables': executables,
    }

    cx_Freeze.setup(**setup_kwargs)
    for path in updater_build_dir.rglob('Updater.com.exe'):
        path.rename(path.with_suffix(''))
