import multiprocessing
import shutil

from package import package
from package import utils


def main():
    import sys
    if len(sys.argv) == 1:
        sys.argv.append('build')

    labbie_proc = multiprocessing.Process(target=package.package_labbie)
    updater_proc = multiprocessing.Process(target=package.package_updater)

    labbie_proc.start()
    updater_proc.start()

    labbie_proc.join()
    updater_proc.join()

    root_dir = utils.root_dir()
    build_dir = utils.build_dir() / 'Labbie'
    lib_dir = build_dir / 'lib'

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    lib_dir.mkdir()

    labbie_build_dir = utils.labbie_build_dir()
    updater_build_dir = utils.updater_build_dir()
    tesseract_dir = root_dir / 'bin' / 'tesseract'

    shutil.copytree(labbie_build_dir, build_dir / 'bin' / 'labbie', dirs_exist_ok=True)
    shutil.copytree(updater_build_dir, build_dir / 'bin' / 'updater', dirs_exist_ok=True)
    shutil.copytree(tesseract_dir, build_dir / 'bin' / 'tesseract', dirs_exist_ok=True)
    shutil.move(str(build_dir / 'bin' / 'labbie' / 'lib' / 'PySide2'), build_dir / 'lib')
    shutil.move(str(build_dir / 'bin' / 'labbie' / 'lib' / 'shiboken2'), build_dir / 'lib')
    shutil.copy(root_dir / 'README.md', build_dir / 'README.md')
    shutil.copytree(root_dir / 'config', build_dir / 'config', dirs_exist_ok=True)


if __name__ == '__main__':
    main()
