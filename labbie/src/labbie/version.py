from typing import Tuple

__version__ = '0.7.0-alpha.4'

_PRERELEASE_TYPE_VALUE = {
    None: 1000,
    'alpha': 0,
    'beta': 1,
    'rc': 2
}
_PRERELEASE_VALUE_TYPE = {
    v: k for k, v in _PRERELEASE_TYPE_VALUE.items()
}


def to_tuple(version: str):
    version_number = []
    core, *prerelease = version.split('-')
    for part in core.split('.'):
        version_number.append(int(part))

    if prerelease:
        prerelease_type, *prerelease_version = prerelease[0].split('.')
        if not prerelease_version:
            raise ValueError(f'Invalid prerelease version, missing prerelease version number: {prerelease}')

        try:
            version_number.append(_PRERELEASE_TYPE_VALUE[prerelease_type])
        except KeyError:
            raise ValueError(f'Invalid prerelease version, invalid type: {prerelease}')
        version_number.append(int(prerelease_version[0]))
    else:
        version_number.append(_PRERELEASE_TYPE_VALUE[None])
        version_number.append(0)

    return tuple(version_number)


def from_tuple(version_number: Tuple[int, int, int, int, int]):
    major, minor, patch, prerelease_type_value, prerelease_version = version_number
    prerelease_type = _PRERELEASE_VALUE_TYPE[prerelease_type_value]
    prerelease = '' if prerelease_type is None else f'-{prerelease_type}.{prerelease_version}'
    return f'{major}.{minor}.{patch}{prerelease}'


VERSION_NUMBER = to_tuple(__version__)
