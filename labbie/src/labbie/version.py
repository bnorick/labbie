__version__ = '0.7.0-alpha.1'

from typing import Tuple

_PRERELEASE_TYPE_VALUE = {
    None: 1000,
    'alpha': 0,
    'beta': 1,
    'rc': 2
}
_PRERELEASE_VALUE_TYPE = {
    v: k for k, v in _PRERELEASE_TYPE_VALUE.items()
}

VERSION_NUMBER = []
_version, *_prerelease = __version__.split('-')
for part in _version.split('.'):
    VERSION_NUMBER.append(int(part))

if _prerelease:
    prerelease_type, *prerelease_version = _prerelease[0].split('.')
    if not prerelease_version:
        raise ValueError(f'Invalid prerelease version, missing prerelease version number: {_prerelease}')

    try:
        VERSION_NUMBER.append(_PRERELEASE_TYPE_VALUE[prerelease_type])
    except KeyError:
        raise ValueError(f'Invalid prerelease version, invalid type: {_prerelease}')
    VERSION_NUMBER.append(int(prerelease_version[0]))
else:
    VERSION_NUMBER.append(_PRERELEASE_TYPE_VALUE[None])
    VERSION_NUMBER.append(0)

VERSION_NUMBER = tuple(VERSION_NUMBER)


def from_tuple(version_number: Tuple[int, int, int, int, int]):
    major, minor, patch, prerelease_type_value, prerelease_version = version_number
    prerelease_type = _PRERELEASE_VALUE_TYPE[prerelease_type_value]
    prerelease = '' if prerelease_type is None else f'-{prerelease_type}.{prerelease_version}'
    return f'{major}.{minor}.{patch}{prerelease}'
