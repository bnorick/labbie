import multiprocessing

from package import package


def run():
    labbie_proc = multiprocessing.Process(target=package.package_labbie)
    updater_proc = multiprocessing.Process(target=package.package_updater)

    labbie_proc.start()
    updater_proc.start()

    labbie_proc.join()
    updater_proc.join()


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        sys.argv.append('build')

    run()
