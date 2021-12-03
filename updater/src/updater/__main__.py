import argparse
import asyncio
import atexit
import pathlib
import shutil
import sys
import tempfile
import traceback
from typing import Callable, Optional, Tuple

import loguru
from qtpy import QtGui
from qtpy import QtWidgets
import qasync
from tuf import settings
from tuf import exceptions
from tuf.client import updater

from labbie import ipc
from updater import components
from updater import config
from updater import constants
from updater import diff_utils
from updater import errors
from updater import patch
from updater import paths
from updater import signals
from updater import utils
from updater import versions
from updater.ui import update_window
from updater.vendor.qtmodern import styles

logger = loguru.logger


def prerelease_reversion_target(component: components.Component, prerelease: versions.Version):
    # e.g., labbie/v0_8_0-rc_3.patch.rollback
    return target(component, prerelease) + '.rollback'


def target(component: components.Component, version: versions.Version):
    # e.g., labbie/v0_8_0.patch
    return f'{component.name.lower()}/v{version.path_encoded()}.patch'


def compatible_prerelease_versions(version_from: versions.Version, version_to: versions.Version):
    """Checks two prerelease versions for compatibility."""
    if not version_from.is_prerelease() or not version_to.is_prerelease():
        return False
    return version_from.core == version_to.core


def get_versions(component: components.Component, release_type: str) -> Tuple[versions.Version, versions.Version]:
    current = component.version
    logger.info(f'current version: {current}')
    latest = component.latest_version(release_type)
    return current, latest


def calculate_target_names(component: components.Component, version_from: versions.Version, version_to: versions.Version):
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
    except errors.NoSuchRelease:
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


async def update(component: components.Component, paths: paths.Paths, release_type: str,
                 callback: Optional[Callable] = None, sync: bool = False):
    if callback is None:
        def callback(**kwargs):
            pass

    try:

        @utils.wrap
        def start(component):
            component.load()

        await start(component)

        current, latest = get_versions(component, release_type)
        callback(message=f'Current version: {current}\nLatest {release_type}: {latest}')

        if current == latest:
            callback(message='Already up to date.', progress=100)
        elif utils.should_skip_version(latest):
            callback(message='Version is marked skipped.', progress=100)
        else:

            def clean(paths):
                cleanup(paths)

            def copy(component, temp_dir):
                shutil.copytree(component.path, temp_dir, dirs_exist_ok=True)

            def download(updater, target, destination):
                updater.download_target(target, destination)

            def apply(source, patch_path: pathlib.Path):
                with patch_path.open('rb') as f:
                    patch.apply_patch(source, f)

            def replace(current_path: pathlib.Path, old_path: pathlib.Path, new_path: str):
                if old_path.exists():
                    diff_utils.really_rmtree(str(old_path))
                diff_utils.really_rename(str(current_path), str(old_path))
                shutil.move(new_path, str(current_path))

            if not sync:
                clean = utils.wrap(clean)
                copy = utils.wrap(copy)
                download = utils.wrap(download)
                apply = utils.wrap(apply)
                replace = utils.wrap(replace)

            progress = 0
            callback(message='Preparing to download and apply updates...', progress=progress)
            if sync:
                cleanup(paths)
            else:
                await clean(paths)
            progress += 5

            repo_dir = paths.repo
            settings.repositories_directory = str(repo_dir.parent)
            logger.info(f'Loading repository from local={repo_dir} remote={component.repository_url}')

            updater_ = updater.Updater(repo_dir.name, component.repository_mirrors)
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

            try:
                targets = [updater_.get_one_valid_targetinfo(t) for t in target_names]
                updated_targets = updater_.updated_targets(targets, destination_directory)

                paths.work.mkdir(parents=True, exist_ok=True)
                temp_dir = tempfile.mkdtemp(dir=paths.work)
                callback(message='Copying source files...', progress=progress)
                if sync:
                    copy(component, temp_dir)
                else:
                    await copy(component, temp_dir)
                progress += 10

                for index, target in enumerate(updated_targets, start=1):
                    message = f'Downloading {target["filepath"]} ({index} / {total})...'
                    callback(message=message, progress=progress)
                    logger.info(message)
                    if sync:
                        download(updater_, target, destination_directory)
                    else:
                        await download(updater_, target, destination_directory)
                    progress += per_action

                    message = f'Applying {target["filepath"]}...'
                    logger.info(message)
                    callback(message=message, progress=progress)
                    try:
                        if sync:
                            apply(temp_dir, paths.downloads / target['filepath'])
                        else:
                            await apply(temp_dir, paths.downloads / target['filepath'])
                    except patch.PatchError as e:
                        message = f'Error while applying patch ({e}).'
                        logger.exception(message)
                        raise errors.Error(message)
                    progress += per_action

                current_path = component.path
                old_version_path = component.path.with_name(f'{component.name.lower()} {component.version}')
                if not component.replace_after_exit:
                    if component.is_running():
                        future = asyncio.Future()
                        callback(signal=signals.Signal.COMPONENT_IS_RUNNING, data=(component, future))
                        await future

                    message = (f'Replacing {component.name} v{current} with {component.name} '
                               f'v{latest}...')
                    logger.info(message)
                    callback(message=message, progress=progress)
                    if sync:
                        replace(current_path, old_version_path, temp_dir)
                    else:
                        await replace(current_path, old_version_path, temp_dir)
                else:
                    message = (f'Registering action to replace {component.name} v{current} with '
                               f'{component.name} v{latest}...')
                    logger.info(message)
                    callback(message=message, progress=progress)

                    def rename():
                        utils.rename_later(path_from=current_path, path_to=old_version_path, delay=1)
                        utils.rename_later(path_from=pathlib.Path(temp_dir), path_to=current_path, delay=2)
                    atexit.register(rename)
                progress += 5 + extra
                callback(message='Done.', progress=progress)

            except exceptions.UnknownTargetError as e:
                logger.exception('Update failed')
                callback(message=f'Update failed, error:\n{e}', error=True)
            except errors.Error as e:
                logger.exception('Update failed')
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--release', action='store_true')
    group.add_argument('--prerelease', action='store_true')
    parser.add_argument('--data-dir', type=utils.resolve_path, default=None)
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

    paths = utils.get_paths(data_dir=constants.LABBIE_CONSTANTS.data_dir)

    valid_components = components.COMPONENTS

    def labbie_is_running():
        return ipc.is_running()

    def labbie_close_and_continue(future):
        async def task():
            ipc.signal_exit()
            await ipc.wait_for_exit_async()
            # TODO(bnorick): this arbitrary sleep seems uneeded, just figure out what exception to handle in
            # the filesystem manipulation, but I am too tired
            await asyncio.sleep(0.5)
            future.set_result(None)
        asyncio.create_task(task())

    valid_components['labbie'].set_running_handlers(labbie_is_running, labbie_close_and_continue)

    component = valid_components[args.component]
    if args.prerelease or args.release:
        release_type = 'prerelease' if args.prerelease else 'release'
        logger.info(f'Using explicitly set release type: {release_type=}')
    elif args.component == 'labbie':
        release_type = 'prerelease' if config.LABBIE_CONFIG.updates.install_prereleases else 'release'
        logger.info(f'Using release type from Labbie config: {release_type=}')
    else:
        release_type = 'release'
        logger.info(f'Using default release type: {release_type=}')

    if args.action == 'check':
        component.load()
        current, latest = get_versions(component, release_type)
        if current != latest:
            print(str(latest), end='')
        sys.exit()

    app = QtWidgets.QApplication(sys.argv)
    styles.dark(app)

    utils.fix_taskbar_icon()
    icon_path = utils.assets_dir() / 'icon.ico'
    app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    show_launch_labbie = args.component == 'labbie'
    window = update_window.UpdateWindow(show_launch_labbie=show_launch_labbie)
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
