import dataclasses
from typing import Optional, Tuple

_PRERELEASE_TYPE_VALUE = {
    None: 1000,
    'alpha': 0,
    'beta': 1,
    'rc': 2
}
_PRERELEASE_VALUE_TYPE = {
    v: k for k, v in _PRERELEASE_TYPE_VALUE.items()
}


@dataclasses.dataclass(frozen=True)
class Version:
    """The version."""
    version: str
    """The version as a tuple."""
    version_tuple: Tuple[int, int, int, int, int] = dataclasses.field(init=False)
    """Index in history of all versions."""
    index: Optional[int] = dataclasses.field(compare=False, default=None)

    def __post_init__(self):
        object.__setattr__(self, 'version_tuple', Version.tuple_from_str(self.version))

    @property
    def core(self):
        # core-prerelease, as per semver.org
        return self.version.split('-')[0]

    def is_prerelease(self):
        # core-prerelease, as per semver.org
        return '-' in self.version

    def path_encoded(self):
        return self.version.replace('.', '_')

    @classmethod
    def from_tuple(cls, version_tuple: Tuple[int, int, int, int, int], index: Optional[int] = None):
        return cls(version=Version.str_from_tuple(version_tuple), index=index)

    @staticmethod
    def tuple_from_str(version: str):
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

    @staticmethod
    def str_from_tuple(version_number: Tuple[int, int, int, int, int]):
        major, minor, patch, prerelease_type_value, prerelease_version = version_number
        prerelease_type = _PRERELEASE_VALUE_TYPE[prerelease_type_value]
        prerelease = '' if prerelease_type is None else f'-{prerelease_type}.{prerelease_version}'
        return f'{major}.{minor}.{patch}{prerelease}'

    def __str__(self):
        return self.version

    def __gt__(self, other: 'Version'):
        if not isinstance(other, (Version, str)):
            return NotImplemented

        other_tuple = other.version_tuple if isinstance(other, Version) else Version.tuple_from_str(other)
        return self.version_tuple > other_tuple

    def __lt__(self, other: 'Version'):
        if not isinstance(other, (Version, str)):
            return NotImplemented

        other_tuple = other.version_tuple if isinstance(other, Version) else Version.tuple_from_str(other)
        return self.version_tuple < other_tuple
