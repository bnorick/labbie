import argparse
import json

import loguru
import requests
from tuf import settings
from tuf import exceptions
from tuf.client import updater

from updater import utils

logger = loguru.logger


class Error(Exception):
    pass


class NoSuchRelease(Error):
    pass


def is_prerelease(version):
    return 'rc' in version


def previous_release(index_from, versions):
    for index in range(index_from - 1, 0, -1):
        version = versions[index]
        if not is_prerelease(version):
            return index, version
    raise NoSuchRelease


def next_release(index_from, versions):
    for index in range(index_from + 1, len(versions)):
        version = versions[index]
        if not is_prerelease(version):
            return index, version
    raise NoSuchRelease


def next_sequential_prerelease(index_from, versions):
    index = index_from + 1
    if index == len(versions):
        raise NoSuchRelease
    version = versions[index]
    if is_prerelease(version):
        return index, version
    raise NoSuchRelease


def prerelease_reversion_target(prerelease):
    # e.g., v0_8_0-rc_3.reversion.patch
    return f'v{prerelease.replace(".", "_")}.reversion.patch'


def target(version):
    return f'v{version.replace(".", "_")}.patch'


def compatible_prerelease_versions(version_from, version_to):
    """Checks two prerelease versions for compatibility."""
    if not is_prerelease(version_from) or not is_prerelease(version_to):
        return False
    return version_from.split('-')[0] == version_to.split('-')[0]


def calculate_target_names(versions, version_from, version_to):
    targets = []
    index = versions.index(version_from)
    version = version_from
    if compatible_prerelease_versions(version_from, version_to):
        while version != version_to:
            index, version = next_sequential_prerelease(index, versions)
            targets.append(target(version))
        return targets

    if is_prerelease(version_from):
        targets.append(prerelease_reversion_target(version_from))
        _, previous_release_version = previous_release(version_from, versions)
        if previous_release_version == version_to:
            return targets

    try:
        # Follow the chain of releases until we arrive at the version we are upgrading to or
        # it is exhausted.
        while version != version_to:
            index, version = next_release(index, versions)
            targets.append(target(version))
    except NoSuchRelease:
        # We reached the last release without reaching version_to, meaning we must be updating to
        # a prerelease. Follow the chain of prereleases from the last release.
        assert is_prerelease(version_to)
        while version != version_to:
            index, version = next_sequential_prerelease(index, versions)
            targets.append(target(version))

    return targets


def update(type_):
    resp = requests.get('https://labbie.blob.core.windows.net/releases/version_history.json')
    version_history = resp.json()
    versions = version_history['all']

    current = utils.get_labbie_version()
    latest_release = version_history['latest']['release']
    latest_prerelease = version_history['latest']['prerelease']

    latest_release_index = versions.index(latest_release)
    latest_prerelease_index = versions.index(latest_prerelease)

    # remove versions beyond the latest latest_x from consideration
    versions = versions[:max(latest_release_index, latest_prerelease_index) + 1]

    logger.info(f'versions: {current=} {latest_release=} {latest_prerelease=}')

    # when a release exists which is newer than the latest prerelease, we ignore prereleases
    if type_ == 'prerelease' and latest_prerelease_index < latest_release_index:
        type_ = 'release'

    latest = latest_release if type_ == 'release' else latest_prerelease

    if current != latest:
        settings.repositories_directory = utils.root_dir()
        repository_mirrors = {'mirror1': {'url_prefix': 'http://localhost:8001',
                                            'metadata_path': 'metadata',
                                            'targets_path': 'targets'}}

        repo_dir = utils.repository_path()
        logger.info(f'Loading repository from {repo_dir}')

        updater_ = updater.Updater(str(repo_dir), repository_mirrors)
        updater_.refresh()

        destination_directory = str(utils.root_dir() / 'data' / 'updates')

        target_names = calculate_target_names(versions, current, latest)
        logger.info(f'Updating from {current=} to {latest=} with the path: {target_names}')

        try:
            targets = [updater_.get_one_valid_targetinfo(t) for t in target_names]
            updated_targets = updater_.updated_targets(targets, destination_directory)
            for target in updated_targets:
                updater_.download_target(target, destination_directory)
        except exceptions.UnknownTargetError as e:
            logger.error(f'Update failed, {e}')


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
    return parser.parse_args()


def main():
    logger.add(utils.root_dir() / 'logs' / 'updater.log', mode='w', encoding='utf8')

    args = parse_args()
    type_ = 'prerelease' if args.prerelease else 'release'
    update(type_)


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
