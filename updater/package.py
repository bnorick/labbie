# -*- coding: utf-8 -*-
import pathlib

import cx_Freeze
import setuptools

package_dir = {'': 'src'}
packages = setuptools.find_packages('src')
package_data = {'': ['*']}

install_requires = [
    'cryptography>=35.0.0,<36.0.0',
    'requests>=2.26.0,<3.0.0',
    'tuf>=0.19.0,<0.20.0'
]

build_exe_options = {
    'packages': packages,
    'include_files': ['repo', 'assets', 'LICENSE'],
    'excludes': ['tkinter', 'test', 'labbie', 'PyQt5', 'PySide2'],
    # 'includes': ['cryptography', 'tuf', 'requests', 'pathlib', 'subprocess', 'sys', 'loguru', 'argparse', 'json'],
    'optimize': 2
}

executables = [
    cx_Freeze.Executable(
        'entry_point.py',
        base='Win32GUI',
        icon='assets/icon.ico',
        target_name='Updater.exe'
    ),
    cx_Freeze.Executable(
        'entry_point.py',
        base=None,
        target_name='Updater.com'
    )
]

setup_kwargs = {
    'name': 'updater',
    'version': '0.1.0',
    'description': 'Auto Updater for Labbie',
    'long_description': None,
    'author': 'Brandon Norick',
    'author_email': 'b.norick@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
    'options': {
        'build_exe': build_exe_options
    },
    'executables': executables,
}


def package():
    import sys
    if len(sys.argv) == 1:
        sys.argv.append('build')
    cx_Freeze.setup(**setup_kwargs)
    build_dir = pathlib.Path(__file__).parent / 'build'
    for path in build_dir.rglob('Updater.com.exe'):
        path.rename(path.with_suffix(''))


if __name__ == '__main__':
    package()
