import asyncio
import pathlib
import sys

import injector
import loguru
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import qasync

from labbie import config
from labbie import constants
from labbie import enchants
from labbie import errors
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


def main():
    logger.remove()
    log_path = utils.root_dir() / 'logs' / 'current_run.log'
    if log_path.is_file():
        prev_log_path = log_path.with_name('prev_run.log')
        if prev_log_path.is_file():
            prev_log_path.unlink()
        log_path.rename(prev_log_path)
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


async def start(log_filter):
    injector = _Injector(_Module())

    constants = injector.get(_Constants)

    if constants.debug:
        log_filter.level = 'DEBUG'

    # ensure directories exist
    (constants.data_dir / 'screenshots').mkdir(parents=True, exist_ok=True)
    (constants.data_dir / 'league').mkdir(parents=True, exist_ok=True)
    (constants.data_dir / 'daily').mkdir(parents=True, exist_ok=True)

    config = injector.get(_Config)
    app_state = injector.get(state.AppState)
    if config.league:
        league_path = constants.data_dir / 'league'
        try:
            app_state.league_enchants.load(league_path)
        except errors.EnchantDataNotFound:
            app_state.last_error = 'Unable to load league enchants'
            app_state.state = state.State.ERROR
            logger.error('Unable to load league enchants')
        if app_state.league_enchants.refresh_needed():
            asyncio.create_task(download(league_path, constants, app_state, app_state.league_enchants))

    if config.daily:
        daily_path = constants.data_dir / 'daily'
        try:
            app_state.daily_enchants.load(daily_path)
        except errors.EnchantDataNotFound:
            app_state.last_error = 'Unable to load daily enchants'
            app_state.state = state.State.ERROR
            logger.error('Unable to load daily enchants')
        if app_state.daily_enchants.refresh_needed():
            asyncio.create_task(download(daily_path, constants, app_state, app_state.daily_enchants))

    app_presenter = injector.get(app.AppPresenter)
    app_presenter.launch()


async def download(path: pathlib.Path, constants: _Constants, app_state: state.AppState, curr_enchants: enchants.Enchants):
    try:
        await enchants.download(path, curr_enchants, constants.user_agent)
    except errors.EnchantDataNotFound:
        app_state.last_error = f'Unable to download recent {curr_enchants.type} enchant data'
        app_state.state = state.State.ERROR
        logger.error(f'Unable to download recent {curr_enchants.type} enchant data')


if __name__ == '__main__':
    main()
