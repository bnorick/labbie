import argparse
import asyncio
import atexit
import dataclasses
import functools
import pathlib
import shutil
import sys
import tempfile
import traceback
from typing import Callable, List, Optional

import loguru
from qtpy import QtGui
from qtpy import QtWidgets
import qasync
import requests
from tuf import settings
from tuf import exceptions
from tuf.client import updater

from labbie import constants
from labbie import ipc
from updater import patch
from updater import paths
from updater import signals
from updater import utils
from updater import version
from updater.ui import update_window
from updater.vendor.qtmodern import styles

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
        self._version_name = version_name

    def set_running_handlers(self, is_running, close_and_continue):
        self.is_running = is_running
        self.close_and_continue = close_and_continue

    def load(self):
        version_name = self._version_name

        try:
            self._version_name_to_id = {version.name: version.id for version in self.versions}
        except Error as e:
            logger.error(str(e))
            raise

        if self.version is None:
            if version_name is None:
                raise ValueError('Invalid arguments, either version must be set to a Version or '
                                 'version_name must be specified.')
            self.version = Version(name=version_name, id=self._version_name_to_id[version_name])

        # clip versions to end at the last "latest"
        try:
            last_id = max(self._version_name_to_id[v] for v in self.version_history['latest'].values())
        except ValueError:
            raise ValueError(f'Invalid version_history at {self.version_history_url}, no latest versions.')
        self.versions = self.versions[:last_id + 1]
        self._version_name_to_id = {version.name: version.id for version in self.versions}

    @functools.cached_property
    def version_history(self):
        resp = requests.get(self.version_history_url)
        if resp.status_code != 200:
            raise Error(f'Unable to download version history for component {self.name} from '
                        f'{self.version_history_url}.')
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
        return self.versions[self._version_name_to_id[latest]]

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
        version = self.versions[version_from.id + 1]
        if version.is_prerelease():
            return version
        raise NoSuchRelease


def prerelease_reversion_target(component: Component, prerelease: Version):
    # e.g., labbie/v0_8_0-rc_3.patch.rollback
    return target(component, prerelease) + '.rollback'


def target(component: Component, version: Version):
    # e.g., labbie/v0_8_0.patch
    return f'{component.name.lower()}/v{version.name.replace(".", "_")}.patch'


def compatible_prerelease_versions(version_from: Version, version_to: Version):
    """Checks two prerelease versions for compatibility."""
    if not version_from.is_prerelease() or not version_to.is_prerelease():
        return False
    return version_from.core == version_to.core


def get_versions(component: Component, release_type: str):
    current = component.version
    latest_release = component.latest_version('release')
    latest_prerelease = component.latest_version('prerelease')

    # when a release exists which is newer than the latest prerelease, we ignore prereleases
    release_newer = latest_prerelease is None or latest_prerelease.id < latest_release.id
    if release_type == 'prerelease' and release_newer:
        release_type = 'release'

    latest = latest_release if release_type == 'release' else latest_prerelease
    logger.info(f'versions: {current=} {latest_release=} {latest_prerelease=} {latest=}')
    return current, latest


def calculate_target_names(component: Component, version_from: Version, version_to: Version):
    targets = []
    version = version_from
    if compatible_prerelease_versions(version_from, version_to):
        while version != version_to:
            version = component.next_sequential_prerelease(version)
            targets.append(target(component, version))
        return targets

    if version_from.is_prerelease():
        targets.append(prerelease_reversion_target(component, version_from))
        previous_release_version = component.previous_release(version_from)
        if previous_release_version == version_to:
            return targets

    try:
        # Follow the chain of releases until we arrive at the version we are upgrading to or
        # it is exhausted.
        while version != version_to:
            version = component.next_release(version)
            targets.append(target(component, version))
    except NoSuchRelease:
        # We reached the last release without reaching version_to, meaning we must be updating to
        # a prerelease. Follow the chain of prereleases from the last release.
        assert version_to.is_prerelease()
        while version != version_to:
            version = component.next_sequential_prerelease(version)
            targets.append(target(component, version))

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


async def update(component: Component, paths: paths.Paths, release_type: str,
                 callback: Optional[Callable] = None):
    if callback is None:
        def callback(**kwargs):
            pass

    try:

        @utils.wrap
        def start(component):
            component.load()

        await start(component)

        current, latest = get_versions(component, release_type)
        callback(message=f'Current version: {current.name}\nLatest {release_type}: {latest.name}')

        if current == latest:
            callback(message='Already up to date.', progress=100)
        else:
            progress = 0
            callback(message='Preparing to download and apply updates...', progress=progress)
            await utils.wrap(cleanup)(paths)
            progress += 5

            repo_dir = paths.repo
            settings.repositories_directory = str(repo_dir.parent)
            logger.info(f'Loading repository from local={repo_dir} remote={component.repository_url}')

            repository_mirrors = {
                'mirror1': {
                    'url_prefix': component.repository_url,
                    'metadata_path': 'metadata',
                    'targets_path': 'targets'
                }
            }

            updater_ = updater.Updater(repo_dir.name, repository_mirrors)
            callback(message='Refreshing patch information...', progress=progress)
            updater_.refresh()
            progress += 2

            destination_directory = str(paths.downloads)

            callback(message='Calculating which patches to apply...', progress=progress)
            target_names = calculate_target_names(component, current, latest)
            progress += 3
            logger.info(f'Downloading and applying updates from {current=} to {latest=} with the '
                        f'path: {target_names}')

            total = len(target_names)
            remainder = 100 - progress - 5 - 10
            per_action = remainder // (total * 2)  # * 2 for download and apply
            extra = remainder - per_action * total * 2

            @utils.wrap
            def copy(component, temp_dir):
                shutil.copytree(component.path, temp_dir, dirs_exist_ok=True)

            @utils.wrap
            def download(updater, target, destination):
                updater.download_target(target, destination)

            @utils.wrap
            def apply(source, patch_path: pathlib.Path):
                with patch_path.open('rb') as f:
                    patch.apply_patch(source, f)

            @utils.wrap
            def replace(current_path: pathlib.Path, old_path: pathlib.Path, new_path: str):
                if old_path.exists():
                    shutil.rmtree(str(current_path))
                else:
                    shutil.move(str(current_path), str(old_path))
                shutil.move(new_path, str(current_path))

            try:
                targets = [updater_.get_one_valid_targetinfo(t) for t in target_names]
                updated_targets = updater_.updated_targets(targets, destination_directory)

                paths.work.mkdir(parents=True, exist_ok=True)
                temp_dir = tempfile.mkdtemp(dir=paths.work)
                callback(message='Copying source files...', progress=progress)
                await copy(component, temp_dir)
                progress += 10

                for index, target in enumerate(updated_targets, start=1):
                    message = f'Downloading {target["filepath"]} ({index} / {total})...'
                    callback(message=message, progress=progress)
                    logger.info(message)
                    await download(updater_, target, destination_directory)
                    # updater_.download_target(target, destination_directory)
                    progress += per_action

                    message = f'Applying {target["filepath"]}...'
                    logger.info(message)
                    callback(message=message, progress=progress)
                    try:
                        await apply(temp_dir, paths.downloads / target['filepath'])
                    except patch.PatchError as e:
                        message = f'Error while applying patch ({e}).'
                        logger.exception(message)
                        raise Error(message)
                    progress += per_action

                current_path = component.path
                old_version_path = component.path.with_name(
                    f'{component.name.lower()} {component.version.name}')
                if not component.replace_after_exit:
                    if component.is_running():
                        future = asyncio.Future()
                        callback(signal=signals.Signal.COMPONENT_IS_RUNNING, data=(component, future))
                        await future

                    message = (f'Replacing {component.name} v{current.name} with {component.name} '
                               f'v{latest.name}...')
                    logger.info(message)
                    callback(message=message, progress=progress)
                    await replace(current_path, old_version_path, temp_dir)
                else:
                    message = (f'Registering action to replace {component.name} v{current.name} with '
                               f'{component.name} v{latest.name}...')
                    logger.info(message)
                    callback(message=message, progress=progress)

                    def rename():
                        utils.rename_later(path_from=current_path, path_to=old_version_path, delay=1)
                        utils.rename_later(path_from=temp_dir, path_to=current_path, delay=2)
                    atexit.register(rename)
                progress += 5 + extra
                callback(message='Done.', progress=progress)

            except exceptions.UnknownTargetError as e:
                logger.error(f'Update failed, {e}')
                callback(message=f'Update failed, error:\n{e}', error=True)
            except Error as e:
                logger.error(f'Update failed, {e}')
                callback(message=f'Update failed, error:\n{e}', error=True)
            except Exception as e:
                logger.exception('Unknown error')
                tb = traceback.format_exc()
                callback(message=f'Update failed with unknown error, please report this to @Cubed#7363 on Discord.\n{e}\n{tb}', error=True)
    except asyncio.CancelledError:
        callback(message='Update cancelled.', error=True)
        raise


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--update', dest='action', action='store_const', const='update')
    group.add_argument('--check', dest='action', action='store_const', const='check')
    parser.add_argument('--component', default='labbie')
    parser.add_argument('--prerelease', action='store_true')
    parser.add_argument('--data-dir', type=utils.resolve_path, default=None)
    parser.add_argument('--current-version', default=None)
    args = parser.parse_args()
    if args.action is None:
        args.action = 'update'
    return args


def main():
    args = parse_args()
    if args.action == 'check':
        logger.remove()
    else:
        logger.add(utils.root_dir() / 'logs' / 'updater.log', mode='w', encoding='utf8')

    constants_ = constants.Constants.load()
    paths = utils.get_paths(data_dir=constants_.data_dir)

    components = {
        'labbie': Component(
            'Labbie',
            path=utils.built_labbie_dir(),
            version_history_url='https://labbie.blob.core.windows.net/releases/components/labbie/version_history.json',
            repository_url='https://labbie.blob.core.windows.net/releases',
            version_name=args.current_version or utils.get_labbie_version()
        ),
        'updater': Component(
            'Updater',
            path=utils.built_updater_dir(),
            version_history_url='https://labbie.blob.core.windows.net/releases/components/updater/version_history.json',
            repository_url='https://labbie.blob.core.windows.net/releases',
            version_name=version.__version__,
            replace_after_exit=True
        )
    }

    def labbie_is_running():
        return ipc.is_running()

    def labbie_close_and_continue(future):
        async def task():
            mm = ipc.instances_shm()
            ipc.signal_exit(mm)
            while ipc.should_exit(mm):
                await asyncio.sleep(0.05)
            future.set_result(None)
        asyncio.create_task(task())

    components['labbie'].set_running_handlers(labbie_is_running, labbie_close_and_continue)

    component = components[args.component]
    release_type = 'prerelease' if args.prerelease else 'release'

    if args.action == 'check':
        component.load()
        current, latest = get_versions(component, release_type)
        if current != latest:
            print(latest.name, end='')
        sys.exit()

    app = QtWidgets.QApplication(sys.argv)
    styles.dark(app)

    utils.fix_taskbar_icon()
    icon_path = utils.assets_dir() / 'icon.ico'
    app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    window = update_window.UpdateWindow()
    window.show()

    def callback(message=None, last=None, error=False, progress=None, signal=None, data=None):
        if last is None:
            last = (progress == 100)

        if message is not None:
            window.add_message(message, last=last, error=error)

        if progress is not None:
            window.set_progress(progress)

        if signal and signal is signals.Signal.COMPONENT_IS_RUNNING:
            component, future = data
            window.ask_to_close(component, future)

    loop = qasync.QSelectorEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        # import logging
        # logging.getLogger("asyncio").setLevel(logging.ERROR)
        if args.action == 'update':
            update_task = loop.create_task(update(component, paths, release_type, callback))
            window.set_task(update_task)
            try:
                loop.run_until_complete(update_task)
                sys.exit(loop.run_forever())
            except asyncio.CancelledError:
                sys.exit(loop.run_forever())
            except RuntimeError as e:
                if str(e) != 'Event loop stopped before Future completed.':
                    raise
                else:
                    update_task.cancel()


if __name__ == '__main__':
    main()
