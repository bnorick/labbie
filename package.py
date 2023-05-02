# -*- coding: utf-8 -*-
import cx_Freeze
import setuptools

package_dir = {'': 'src'}

# packages = [
#     'labbie',
#     'labbie.di',
#     'labbie.ui',
#     'labbie.ui.app',
#     'labbie.ui.result.widget',
#     'labbie.ui.search',
#     'labbie.ui.search.widget',
#     'labbie.ui.search.window',
#     'labbie.ui.settings',
#     'labbie.ui.settings.widget',
#     'labbie.ui.settings.window',
#     'labbie.ui.system_tray',
#     'labbie.vendor.qtmodern'
# ]

packages = setuptools.find_packages('src')

package_data = {'': ['*'], 'labbie': ['vendor/qtmodern/resources/*']}

install_requires = [
    'Pillow>=8.4.0,<9.0.0',
    'PyQt5>=5.15.6,<6.0.0',
    'aiohttp>=3.8.0,<4.0.0',
    'dacite>=1.6.0,<2.0.0',
    'datrie>=0.8.2,<0.9.0',
    'injector>=0.18.4,<0.19.0',
    'keyboard>=0.13.5,<0.14.0',
    'loguru>=0.5.3,<0.6.0',
    'numpy>=1.21.4,<2.0.0',
    'opencv-python-headless>=4.5.4,<5.0.0',
    'orjson>=3.6.4,<4.0.0',
    'pyperclip>=1.8.2,<2.0.0',
    'pytesseract>=0.3.8,<0.4.0',
    'qasync>=0.22.0,<0.23.0',
    'toml>=0.10.2,<0.11.0'
]

setup_kwargs = {
    'name': 'labbie',
    'version': '0.6.0',
    'description': '',
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
    'python_requires': '>=3.8,<3.9',
    'options': {
        'build_exe': {
            # 'packages': ['pygame', 'random', 'ConfigParser', 'sys'],
            'include_files': ['assets', 'bin', 'config', 'README.md', 'LICENSE'],
            'include_msvcr': True
        }
    },
    'executables': [cx_Freeze.Executable('entry_point.py', base='Win32GUI', target_name='Labbie.exe', icon='assets/taxi-32.ico')],
}


def package():
    cx_Freeze.setup(**setup_kwargs)


if __name__ == '__main__':
    package()
