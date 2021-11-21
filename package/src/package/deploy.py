import pathlib
import shutil
import multiprocessing

import loguru
import typer

from labbie_admin.updater import updates
from package import utils
from updater import components
from updater import errors
from updater import patch
from updater import versions

logger = loguru.logger
app = typer.Typer()


def zip(version: versions.Version):
    # zip up for upload to github
    zip_path = utils.build_dir() / f'Labbie_v{version.path_encoded()}.zip'
    shutil.make_archive(str(zip_path), 'zip',  utils.build_dir() / 'Labbie')


def make_patches(historical_dir: pathlib.Path, patches_dir: pathlib.Path, component: components.Component):
    version = component.version

    component_historical_dir = historical_dir / component.name.lower()
    component_historical_dir.mkdir(exist_ok=True)
    component_patches_dir = patches_dir / component.name.lower()
    component_patches_dir.mkdir(exist_ok=True)

    version_dir = component_historical_dir / str(version)
    if version_dir.exists():
        logger.info(f'Version already exists in historical versions: {version_dir}, skipping patch generation')
        return

    if version.is_prerelease():
        prev_version = component.versions[-1]
    else:
        prev_version = component.previous_release(version)

    new_version_dir = component.path
    prev_version_dir = component_historical_dir / str(prev_version)

    patch_path = component_patches_dir / f'v{version.path_encoded()}.patch'
    with patch_path.open('wb') as f:
        patch.write_patch(str(prev_version_dir), str(new_version_dir), f)

    if version.is_prerelease():
        rollback_path = patch_path.with_suffix('.patch.rollback')
        with rollback_path.open('wb') as f:
            patch.write_patch(str(new_version_dir), str(prev_version_dir), f)

    shutil.copytree(new_version_dir, version_dir)


@app.command()
def deploy():
    labbie_component = components.COMPONENTS['labbie']
    labbie_component.load()

    updater_component = components.COMPONENTS['updater']
    updater_component.load()

    zip_proc = None
    if not labbie_component.version.is_prerelease():
        zip_proc = multiprocessing.Process(target=zip, args=(labbie_component.version, ))
        zip_proc.start()

    historical_dir = utils.build_dir() / 'historical'
    historical_dir.mkdir(exist_ok=True)
    patches_dir = utils.build_dir() / 'patches'
    patches_dir.mkdir(exist_ok=True)

    components_to_deploy = [component for component in (labbie_component, updater_component) if component.is_undeployed()]
    patch_procs = []
    for component in components_to_deploy:
        proc = multiprocessing.Process(target=make_patches, args=(historical_dir, patches_dir, component))
        proc.start()
        patch_procs.append(proc)

    for proc in patch_procs:
        proc.join()

    for component in components_to_deploy:
        patches = []
        for patch_file in (patches_dir / component.name.lower()).iterdir():
            if ('v' + component.version.path_encoded()) == patch_file.name.split('.')[0]:
                patches.append(patch_file)

        updates.add_update(component.name.lower(), str(component.version), patches)
