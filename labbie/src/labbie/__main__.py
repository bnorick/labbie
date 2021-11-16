import argparse
import asyncio
import os
import sys

import injector
import loguru
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import qasync

from labbie import config
from labbie import constants
from labbie import resources
from labbie import state
from labbie import utils
from labbie.di import module
from labbie.ui import utils as ui_utils
from labbie.ui.app import presenter as app
from labbie.vendor.qtmodern import styles

logger = loguru.logger
_Module = module.Module
_Injector = injector.Injector
_Config = config.Config
_Constants = constants.Constants


def parse_args():
    parser = argparse.ArgumentParser('Labbie')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()


def main():
    utils.logs_dir().mkdir(exist_ok=True, parents=True)
    utils.exit_if_already_running()

    args = parse_args()
    if args.debug:
        os.environ['LABBIE_DEBUG'] = '1'

    logger.remove()
    log_path = utils.logs_dir() / 'current_run.log'
    if log_path.is_file():
        prev_log_path = log_path.with_name('prev_run.log')
        # delete prev log if it exists
        try:
            prev_log_path.unlink()
        except FileNotFoundError:
            pass
        # move log from last run to prev log
        try:
            log_path.rename(prev_log_path)
        except FileExistsError:
            pass
    log_filter = utils.LogFilter('INFO')
    logger.add(log_path, filter=log_filter, rotation="100 MB", retention=1, mode='w', encoding='utf8')

    app = QtWidgets.QApplication(sys.argv)
    styles.dark(app)
    app.setQuitOnLastWindowClosed(False)

    ui_utils.fix_taskbar_icon()
    icon_path = ui_utils.asset_path('taxi.png')
    app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    loop = qasync.QSelectorEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        loop.run_until_complete(start(log_filter))
        sys.exit(loop.run_forever())


async def focus_if_other_instances(app_presenter):
    mm = utils.instances_shm()
    mm[0] = 1
    while True:
        if mm[0] > 1:
            logger.info(f'instances={mm[0]}')
            app_presenter.foreground()
            mm[0] = 1
        await asyncio.sleep(0.1)


async def start(log_filter):
    injector = _Injector(_Module())

    constants = injector.get(_Constants)

    if constants.debug:
        log_filter.level = 'DEBUG'

    # ensure directories exist
    constants.screenshots_dir.mkdir(parents=True, exist_ok=True)
    (constants.helm_enchants_dir / 'league').mkdir(parents=True, exist_ok=True)
    (constants.helm_enchants_dir / 'daily').mkdir(parents=True, exist_ok=True)

    config = injector.get(_Config)

    resource_manager = injector.get(resources.ResourceManager)
    resource_manager.initialize()
    await resource_manager._init_task

    app_state = injector.get(state.AppState)
    if config.league:
        asyncio.create_task(app_state.league_enchants.download_or_load(constants))
    if config.daily:
        asyncio.create_task(app_state.daily_enchants.download_or_load(constants))

    app_presenter = injector.get(app.AppPresenter)
    app_presenter.launch()
    asyncio.create_task(focus_if_other_instances(app_presenter))


if __name__ == '__main__':
    main()
