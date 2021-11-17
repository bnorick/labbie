import argparse
import dataclasses
import functools
import pathlib
import shutil
import tempfile
from typing import List, Optional

import loguru
import requests
from tuf import settings
from tuf import exceptions
from tuf.client import updater

from updater import patch
from updater import paths
from updater import utils

logger = loguru.logger


class Error(Exception):
    pass


class NoSuchRelease(Error):
    pass


@dataclasses.dataclass(frozen=True)
class Version:
    name: str
    id: int

    def is_prerelease(self):
        return 'rc' in self.name

    @property
    def core(self):
        return self.name.split('-')[0]


@dataclasses.dataclass
class Component:
    name: str
    path: pathlib.Path
    version_history_url: str
    repository_url: str
    version: Version = None
    version_name: dataclasses.InitVar[str] = None
    replace_after_exit: bool = False

    def __post_init__(self, version_name: str):
        if self.version is None:
            if version_name is None:
                raise ValueError('Invalid arguments, either version must be set to a Version or '
                                 'version_name must be specified.')
            self.version = Version(name=version_name, id=self.versions.index(version_name))

        self._version_name_to_id = {version.name: version.id for version in self.versions}

    @functools.cached_property
    def version_history(self):
        resp = requests.get(self.version_history_url)
        return resp.json()

    @functools.cached_property
    def versions(self) -> List[Version]:
        versions = []
        for index, version in enumerate(self.version_history['versions']):
            versions.append(Version(name=version, id=index))
        return versions

    def latest_version(self, type_) -> Optional[Version]:
        latest = self.version_history['latest'].get(type_)
        if latest is None:
            return None
        return self._version_name_to_id[latest]

    def previous_release(self, version_from: Version):
        for index in range(version_from.id - 1, 0, -1):
            version = self.versions[index]
            if not version.is_prerelease():
                return version
        raise NoSuchRelease

    def next_release(self, version_from: Version):
        for index in range(version_from.id + 1, len(self.versions)):
            version = self.versions[index]
            if not version.is_prerelease():
                return version
        raise NoSuchRelease

    def next_sequential_prerelease(self, version_from: Version):
        if version_from == self.versions[-1]:
            raise NoSuchRelease
        version = self.versions[version_from.index + 1]
        if version.is_prerelease():
            return version
        raise NoSuchRelease


def prerelease_reversion_target(prerelease: Version):
    # e.g., v0_8_0-rc_3.reversion.patch
    return f'v{prerelease.name.replace(".", "_")}.reversion.patch'


def target(version: Version):
    return f'v{version.name.replace(".", "_")}.patch'


def compatible_prerelease_versions(version_from: Version, version_to: Version):
    """Checks two prerelease versions for compatibility."""
    if not version_from.is_prerelease() or not version_to.is_prerelease():
        return False
    return version_from.core == version_to.core


def calculate_target_names(component: Component, version_from: Version, version_to: Version):
    targets = []
    version = version_from
    if compatible_prerelease_versions(version_from, version_to):
        while version != version_to:
            version = component.next_sequential_prerelease(version)
            targets.append(target(version))
        return targets

    if version_from.is_prerelease():
        targets.append(prerelease_reversion_target(version_from))
        previous_release_version = component.previous_release(version_from)
        if previous_release_version == version_to:
            return targets

    try:
        # Follow the chain of releases until we arrive at the version we are upgrading to or
        # it is exhausted.
        while version != version_to:
            version = component.next_release(version)
            targets.append(target(version))
    except NoSuchRelease:
        # We reached the last release without reaching version_to, meaning we must be updating to
        # a prerelease. Follow the chain of prereleases from the last release.
        assert version_to.is_prerelease()
        while version != version_to:
            version = component.next_sequential_prerelease(version)
            targets.append(target(version))

    return targets


def delete_contents(directory: pathlib.Path, must_exist=False):
    if not directory.exists():
        if must_exist:
            raise ValueError(f'Invalid argument, expected a directory which exists but {directory} does not.')
        return

    if not directory.is_dir():
        raise ValueError(f'Invalid argument, expected a directory but {directory} is not a directory.')

    logger.info(f'Emptying {directory=}')

    for path in directory.iterdir():
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            raise RuntimeError(f'Cannot remove {path=}')


def cleanup(paths: paths.Paths):
    logger.info(f'Cleaning up {paths.updater_data}')
    delete_contents(paths.downloads)
    delete_contents(paths.work)


def update(component: Component, paths: paths.Paths, release_type: str):
    versions = component.versions

    current = component.version
    latest_release = component.latest_version('release')
    latest_prerelease = component.latest_version('prerelease')

    if release_type == 'prerelease' and (latest_prerelease is None or latest_prerelease.id < latest_release.id):
        release_type = 'release'

    # remove versions beyond the latest latest_x from consideration
    versions = versions[:max(latest_release_index, latest_prerelease_index) + 1]

    logger.info(f'versions: {current=} {latest_release=} {latest_prerelease=}')

    # when a release exists which is newer than the latest prerelease, we ignore prereleases
    if release_type == 'prerelease' and latest_prerelease_index < latest_release_index:
        release_type = 'release'

    latest = latest_release if release_type == 'release' else latest_prerelease

    if current != latest:
        repository_mirrors = {'mirror1': {'url_prefix': 'http://localhost:8001',
                                            'metadata_path': 'metadata',
                                            'targets_path': 'targets'}}

        repo_dir = paths.updater_repo
        settings.repositories_directory = str(repo_dir.parent)
        logger.info(f'Loading repository from {repo_dir}')

        updater_ = updater.Updater(repo_dir.name, repository_mirrors)
        updater_.refresh()

        destination_directory = str(paths.downloads)

        target_names = calculate_target_names(versions, current, latest)
        logger.info(f'Downloading updates from {current=} to {latest=} with the path: {target_names}')

        try:
            targets = [updater_.get_one_valid_targetinfo(t) for t in target_names]
            updated_targets = updater_.updated_targets(targets, destination_directory)

            temp_dir = tempfile.mkdtemp(dir=paths.work)
            shutil.copytree()

            for target in updated_targets:
                updater_.download_target(target, destination_directory)

        except exceptions.UnknownTargetError as e:
            logger.error(f'Update failed, {e}')
            return


def update_self():
    # unpack to bin/updater-vX_Y_Z
    update_path = utils.root_dir() / 'bin' / 'updater-vX_Y_Z'
    current_path = utils.root_dir() / 'bin' / 'updater'
    utils.rename_later(path_from=current_path, path_to=current_path.with_name(f'{current_path.name}-old'), delay=1)
    utils.rename_later(path_from=update_path, path_to=current_path, delay=2)
    exit()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prerelease', action='store_true')
    parser.add_argument('--data-dir', type=utils.resolve_path, default=None)
    return parser.parse_args()


def main():
    logger.add(utils.root_dir() / 'logs' / 'updater.log', mode='w', encoding='utf8')

    args = parse_args()
    paths = utils.get_paths(data_dir=args.data_dir)

    cleanup(paths)

    type_ = 'prerelease' if args.prerelease else 'release'
    update(type_, paths)


if __name__ == '__main__':
    main()

# NG client
# updater_ = updater.Updater(
#     repository_dir=utils.root_dir() / 'updater' / 'metadata' / 'current',
#     metadata_base_url='http://localhost:8001/',
#     target_base_url='http://localhost:8000/targets/',
# )

# updater_.refresh()

# targetinfo = updater.get_one_valid_targetinfo('v0_6_1.patch')
# updater.updated_targets(targetinfo, utils.root_dir() / 'updater' / 'downloads')
