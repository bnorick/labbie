import datetime
from typing import Any, Dict

import loguru
import injector

from labbie import config
from labbie import constants
from labbie import errors
from labbie import ocr
from labbie import result
from labbie import state
from labbie import mods
from labbie.ui import hotkey

logger = loguru.logger
_Config = config.Config
_Constants = constants.Constants
_Result = result.Result
keys = Any  # labbie.ui.keys imports cause circular dependency


@injector.singleton
class AppPresenter:
    @injector.inject
    def __init__(self, constants: _Constants, config: _Config, injector: injector.Injector, app_state: state.AppState, mods: mods.Mods):
        self._constants = constants
        self._config = config
        self._injector = injector
        self._app_state = app_state
        self.mods = mods

        self.presenters = {}

        self._hotkeys: Dict[str, hotkey.Hotkey] = {}
        self._config.ui.hotkeys.attach(self, self._ocr_hotkey_changed, to='ocr')
        self._ocr_hotkey_changed(self._config.ui.hotkeys.ocr)

    def _ocr_hotkey_changed(self, val):
        logger.debug(f'ocr hotkey changed {val=}')
        current_hotkey = self._hotkeys.pop('ocr', None)
        if current_hotkey:
            current_hotkey.stop()

        if val:
            try:
                ocr_hotkey = hotkey.Hotkey(val)
                ocr_hotkey.start(self._ocr_hotkey_pressed)
                self._hotkeys['ocr'] = ocr_hotkey
            except ValueError:
                # May be raised when hotkey can't be bound
                self.show(keys.ErrorWindowKey(Exception(f'Unable to bind hotkey: {val}')))

    def _ocr_hotkey_pressed(self):
        self.screen_capture()

    def reset_window_positions(self):
        key = keys.MainWindowKey()
        if presenter := self.presenters.get(key):
            presenter.reset_position()

    def screen_capture(self):
        if not self._app_state.league_enchants.enabled and not self._app_state.daily_enchants.enabled:
            self.show(keys.ErrorWindowKey('No enchant scrapes are enabled, please edit the settings.'))
            return

        save_path = None
        if self._constants.debug:
            save_path = self._constants.screenshots_dir / datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            save_path.mkdir(exist_ok=True)
        partial_enchant_list = ocr.read_enchants(self._config.ocr.bounds, save_path)
        curr_enchants = self.mods.get_mod_list_from_ocr_results(partial_enchant_list)
        logger.debug(f'{curr_enchants=}')
        results = []
        # TODO: make this work for gloves/boots?
        for index, enchant in enumerate(curr_enchants, start=1):
            logger.debug(f'{index=}: {enchant=}')
            league_matches = None
            if self._app_state.league_enchants.enabled:
                try:
                    league_matches = self._app_state.league_enchants.find_matching_enchants(enchant)
                except errors.EnchantsNotLoaded:
                    self.show(keys.ErrorWindowKey('Enchants have not finished loading.'))
                    return

            daily_matches = None
            if self._app_state.daily_enchants.enabled:
                try:
                    daily_matches = self._app_state.daily_enchants.find_matching_enchants(enchant)
                except errors.EnchantsNotLoaded:
                    self.show(keys.ErrorWindowKey('Enchants have not finished loading.'))
                    return

            if league_matches is not None or daily_matches is not None:
                result = _Result(title=enchant, search=enchant, league_result=league_matches, daily_result=daily_matches, base=False)
                results.append(result)

        if results:
            key = keys.MainWindowKey(results, clear=self._config.ocr.clear_previous)
            self.show(key)
        else:
            key = keys.MainWindowKey()
            self.toggle(key)

    def show(self, key: 'keys._Key'):
        if not isinstance(key, keys._Key):
            raise ValueError(f'{self.__class__.__name__} can only show keys which are instances '
                             f'of WindowKey.')
        if presenter := self.presenters.get(key):
            logger.debug(f'Reusing presenter for {key=}')
            key.show(presenter)
        else:
            logger.debug(f'Getting new presenter for {key=}')
            presenter = key.get_presenter(self._injector)
            self.presenters[key] = presenter
            if key.DELETE_WHEN_CLOSED:
                presenter.add_close_callback(lambda: self.delete(key))
            key.show(presenter)

    def toggle(self, key: 'keys._Key'):
        if not isinstance(key, keys._Key):
            raise ValueError(f'{self.__class__.__name__} can only show keys which are instances '
                             f'of WindowKey.')
        if presenter := self.presenters.get(key):
            logger.debug(f'Reusing presenter for {key=}')
            key.toggle(presenter)
        else:
            self.show(key)

    def delete(self, key):
        logger.debug(f'deleting {key=}')
        self.presenters.pop(key, None)

    def launch(self):
        self.show(keys.SystemTrayIconKey())
        self.show(keys.MainWindowKey())

    def foreground(self):
        self.show(keys.MainWindowKey())

    def shutdown(self):
        self.presenters[keys.SystemTrayIconKey()].exit()


from labbie.ui import keys  # noqa: E402
