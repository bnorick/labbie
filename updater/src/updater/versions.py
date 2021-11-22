import dataclasses

from labbie import version


@dataclasses.dataclass(frozen=True)
class Version:
    """The version."""
    version: str
    """Index in history of all versions."""
    index: int = dataclasses.field(compare=False)

    def is_prerelease(self):
        return '-' in self.version

    def __str__(self):
        return self.version

    @property
    def core(self):
        return self.version.split('-')[0]

    def path_encoded(self):
        return self.version.replace('.', '_')

    def __gt__(self, other: 'Version'):
        if not isinstance(other, (Version, str)):
            return NotImplemented

        version_str = other.version if isinstance(other, Version) else other

        return version.to_tuple(self.version) > version.to_tuple(version_str)

    def __lt__(self, other: 'Version'):
        if not isinstance(other, (Version, str)):
            return NotImplemented

        version_str = other.version if isinstance(other, Version) else other

        return version.to_tuple(self.version) < version.to_tuple(version_str)
