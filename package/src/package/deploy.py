import dataclasses
import multiprocessing
import os
import pathlib
import shutil
import sys
from typing import Callable, List, Optional

import dotenv
import git
import github
import loguru
import pebble
from pebble import concurrent
import typer

from labbie_admin.updater import updates
from package import utils
from updater import components
from updater import errors
from updater import patch
from updater import versions
import updater

logger = loguru.logger
_COMPONENTS = components.COMPONENTS
app = typer.Typer()


class InvalidBranch(Exception):
    pass


def _labbie_branch_validator(version: versions.Version, current_branch: str) -> bool:
    if not version.is_prerelease() and current_branch != 'master':
        raise InvalidBranch(f'Release versions of Labbie must be deployed from the master branch. '
                            f'Current version ({version}) is a release version.')


def _updater_branch_validator(version: versions.Version, current_branch: str) -> bool:
    if current_branch != 'master':
        raise InvalidBranch('Updater must be deployed from the master branch.')


def _labbie_start_extra_tasks(version: versions.Version):
    tasks = []
    if not version.is_prerelease():
        zip_future = make_zip(version)
        tasks.append(zip_future)
    return tasks


@dataclasses.dataclass
class DeployableComponent:
    component: components.Component

    """Optional function to constrain valid branches for deployment.

    Function takes version and current branch and raises `InvalidBranch` for invalid combinations.
    An attempt is made to load from globals (_{component_name}_branch_validator) if not explicitly passed.
    """
    branch_validator: Callable[[versions.Version, str], bool] = ...

    """Function to start additional tasks related to a deployment.

    Function should take version and return a list of multiprocessing `Process`s which have already been started.
    An attempt is made to load from globals (_{component_name}_start_extra_tasks) if not explicitly passed.
    If not found, a no-op is used.
    """
    start_extra_tasks: Callable[[versions.Version], List[pebble.ProcessFuture]] = ...

    def __post_init__(self):
        globals_ = globals()
        if self.branch_validator is Ellipsis:
            self.branch_validator = globals_.get(f'_{self.component.name.lower()}_branch_validator')
            if not self.branch_validator:
                logger.debug(f'No branch validator found for {self.component.name}')

        if self.start_extra_tasks is Ellipsis:
            start_extra_tasks = globals_.get(f'_{self.component.name.lower()}_start_extra_tasks')
            if start_extra_tasks is None:
                logger.debug(f'No extra task source found for {self.component.name}')
                start_extra_tasks = lambda *args, **kwargs: []  # noqa: E731
            self.start_extra_tasks = start_extra_tasks

    def is_deployable(self, repo: git.Repo):
        if not self.component.is_undeployed():
            return False

        if self.branch_validator:
            current_branch = repo.active_branch.name
            try:
                self.branch_validator(self.component.version, current_branch)
            except InvalidBranch as e:
                logger.error(f'Unable to deploy {self.component.name}. {e}')
                return False

        tag_name = f'{self.component.name.lower()}/{self.component.version}'
        tags = {tag.name: tag for tag in repo.tags}
        if (tag := tags.get(tag_name)) and tag.commit != repo.head.commit:
            logger.error(f'Unable to deploy {self.component.name}. Tag "{tag_name}" already exists and '
                         f'references a different commit ({tag.commit}) than HEAD ({repo.head.commit}).')
            return False

        return True


@concurrent.process
def make_zip(version: versions.Version):
    # zip up for upload to github
    zip_path = utils.build_dir() / f'Labbie_v{version.path_encoded()}'
    shutil.make_archive(str(zip_path), 'zip',  utils.build_dir() / 'Labbie')
    return zip_path


@concurrent.process
def make_patches(historical_dir: pathlib.Path, patches_dir: pathlib.Path, component: components.Component):
    version = component.version

    component_historical_dir = historical_dir / component.name.lower()
    component_historical_dir.mkdir(exist_ok=True)
    component_patches_dir = patches_dir / component.name.lower()
    component_patches_dir.mkdir(exist_ok=True)

    version_dir = component_historical_dir / str(version)
    if version_dir.exists():
        logger.info(f'Version already exists in historical versions: {version_dir}, '
                    f'skipping patch generation')
        return

    prev_release = component.previous_release(version)
    try:
        prev_prerelease = component.previous_sequential_prerelease(version)
    except errors.NoSuchRelease:
        prev_prerelease = None

    patch_versions = [(prev_release, version)]
    if prev_prerelease:
        patch_versions.append((prev_prerelease, version))

    if version.is_prerelease():
        patch_versions.append((version, prev_release))

    patch_paths = []
    for version_from, version_to in patch_versions:
        if version_from == component.version:
            prev_version_dir = component.path
        else:
            prev_version_dir = component_historical_dir / str(version_from)

        if version_to == component.version:
            new_version_dir = component.path
        else:
            new_version_dir = component_historical_dir / str(version_to)

        filename = f'{version_from.path_encoded()}_to_{version_to.path_encoded()}.patch'
        patch_path = component_patches_dir / filename
        with patch_path.open('wb') as f:
            patch.write_patch(str(prev_version_dir), str(new_version_dir), f)
        patch_paths.append(patch_path)

    shutil.copytree(component.path, version_dir)
    return patch_paths


@app.command()
def deploy(components: List[str] = typer.Argument(['all'], ), zip: Optional[bool] = None):
    repo = git.Repo(utils.root_dir())
    dotenv.load_dotenv()
    github_repo = github.Github(os.environ.get('GITHUB_TOKEN')).get_repo('bnorick/labbie')

    repo.remotes.origin.update()
    current_branch = repo.active_branch.name

    commits_diff = repo.git.rev_list('--left-right', '--count', f'{current_branch}...{current_branch}@{{u}}')
    num_ahead, num_behind = commits_diff.split('\t')

    if num_ahead or num_behind:
        logger.error(f'Current branch is out of sync with remote branch, {num_behind=} {num_ahead=}. '
                     f'Ensure that the two are in sync before deployment.')
        sys.exit(1)

    if repo.is_dirty():
        logger.error('Local repository is dirty. Deployment can only occur when the local repository is '
                     'clean.')
        sys.exit(1)

    components_to_load = []
    for c in components:
        if c == 'all':
            components_to_load = list(_COMPONENTS.keys())
            break
        if (component := _COMPONENTS.get(c)) is None:
            logger.error(f'Invalid component, "{c}" is not recognized.')
            sys.exit(1)
        components_to_load.append(component)

    for component in components_to_load:
        component.load()

    deployables = [DeployableComponent(c) for c in components_to_load]
    deployables = [d for d in deployables if d.is_deployable(repo)]

    extra_tasks = []
    for d in deployables:
        extra_tasks.extend(d.start_extra_tasks(d.component.version))

    historical_dir = utils.build_dir() / 'historical'
    historical_dir.mkdir(exist_ok=True)
    patches_dir = utils.build_dir() / 'patches'
    patches_dir.mkdir(exist_ok=True)

    patch_futures = [
        make_patches(historical_dir, patches_dir, deployable.component)
        for deployable in deployables
    ]

    for deployable, future in zip(deployables, patch_futures):
        patch_paths = future.result()
        tag_name = f'{deployable.component.name.lower()}/{deployable.component.version}'
        component_tag = repo.create_tag(tag_name)
        repo.remotes.origin.push(component_tag.path)
        release = github_repo.create_git_release(
            tag_name, f'{deployable.component.name} v{deployable.component.version}', 'TODO', draft=True)
        updates.add_update(component.name.lower(), str(component.version), patch_paths)
        for path in patch_paths:
            release.upload_asset(path)

    for task in extra_tasks:
        task.result()
