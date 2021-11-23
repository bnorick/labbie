import dataclasses
import functools
import pathlib
from typing import List, Literal, Optional

import loguru
import requests

from labbie import version as labbie_version
from updater import constants
from updater import errors
from updater import utils
from updater import version
from updater import versions

_Version = versions.Version
logger = loguru.logger


@dataclasses.dataclass
class Component:
    name: str
    path: pathlib.Path
    version_history_url: str
    repository_url: str
    version: _Version = None
    version_str: dataclasses.InitVar[str] = None
    replace_after_exit: bool = False

    def __post_init__(self, version_str: str):
        self._version_str = version_str

    def set_running_handlers(self, is_running, close_and_continue):
        self.is_running = is_running
        self.close_and_continue = close_and_continue

    def load(self):
        version_str = self._version_str

        try:
            self._version_str_to_index = {version.version: version.index for version in self.versions}
        except errors.Error as e:
            logger.error(str(e))
            raise

        if self.version is None:
            if version_str is None:
                raise ValueError('Invalid arguments, either version must be set to a Version or '
                                 'version_str must be specified.')
            self.version = _Version(version=version_str, index=self._version_str_to_index.get(version_str))

        # clip versions to end at the last "latest"
        try:
            last_index = max(self._version_str_to_index[v] for v in self.version_history['latest'].values())
        except ValueError:
            raise ValueError(f'Invalid version_history at {self.version_history_url}, no latest versions.')
        self.versions = self.versions[:last_index + 1]
        self._version_str_to_index = {version.version: version.index for version in self.versions}

    @functools.cached_property
    def version_history(self):
        resp = requests.get(self.version_history_url)
        if resp.status_code != 200:
            raise errors.Error(f'Unable to download version history for component {self.name} from '
                               f'{self.version_history_url}.')
        return resp.json()

    @functools.cached_property
    def versions(self) -> List[_Version]:
        versions = []
        for index, version in enumerate(self.version_history['versions']):
            versions.append(_Version(version=version, index=index))
        return versions

    def is_undeployed(self):
        return self.version > self.versions[-1]

    def latest_typed_version(self, release_type: Literal['release', 'prerelease']) -> Optional[_Version]:
        """Returns the latest version of a specific release type.

        This never opts for another release type if it is newer."""
        latest = self.version_history['latest'].get(release_type)
        if latest is None:
            return None
        return self.versions[self._version_str_to_index[latest]]

    def latest_version(self, release_type: Literal['release', 'prerelease']) -> Optional[_Version]:
        """Returns the latest version for a specific release type.

        If the release type is prerelease and a newer release exists, then the release will be returned."""

        latest_release = self.latest_typed_version('release')
        latest_prerelease = self.latest_typed_version('prerelease')

        # when a release exists which is newer than the latest prerelease, we ignore prereleases
        release_newer = latest_prerelease is None or latest_prerelease.index < latest_release.index
        if release_type == 'prerelease' and release_newer:
            release_type = 'release'

        latest = latest_release if release_type == 'release' else latest_prerelease
        logger.info(f'versions: {latest_release=} {latest_prerelease=} {latest=}')
        return latest

    def previous_release(self, version_from: _Version) -> _Version:
        for version in reversed(self.versions[:version_from.index]):
            if not version.is_prerelease():
                return version
        raise errors.NoSuchRelease

    def next_release(self, version_from: _Version) -> _Version:
        if version_from.index == len(self.versions) - 1:
            raise errors.NoSuchRelease

        for version in self.versions[version_from.index + 1:]:
            if not version.is_prerelease():
                return version
        raise errors.NoSuchRelease

    def previous_sequential_prerelease(self, version_from: _Version) -> _Version:
        if version_from.index == 0:
            raise errors.NoSuchRelease

        version = self.versions[version_from.index - 1]
        if version.is_prerelease():
            return version
        else:
            raise errors.NoSuchRelease

    def next_sequential_prerelease(self, version_from: _Version) -> _Version:
        if version_from.index == len(self.versions) - 1:
            raise errors.NoSuchRelease

        version = self.versions[version_from.index + 1]
        if version.is_prerelease():
            return version
        raise errors.NoSuchRelease


paths = utils.get_paths(data_dir=constants.LABBIE_CONSTANTS.data_dir)

COMPONENTS = {
    'labbie': Component(
        'Labbie',
        path=utils.built_labbie_dir(),
        version_history_url='https://labbie.blob.core.windows.net/releases/components/labbie/version_history.json',
        repository_url='https://labbie.blob.core.windows.net/releases',
        version_str=labbie_version.__version__
    ),
    'updater': Component(
        'Updater',
        path=utils.built_updater_dir(),
        version_history_url='https://labbie.blob.core.windows.net/releases/components/updater/version_history.json',
        repository_url='https://labbie.blob.core.windows.net/releases',
        version_str=version.__version__,
        replace_after_exit=True
    )
}
