import datetime
from typing import Any, Dict

import loguru
import injector

from labbie import config
from labbie import constants
from labbie import enchants
from labbie import errors
from labbie import ocr
from labbie import result
from labbie import state
from labbie.ui import hotkey

logger = loguru.logger
_Config = config.Config
_Constants = constants.Constants
_Result = result.Result
keys = Any  # labbie.ui.keys imports cause circular dependency


@injector.singleton
class AppPresenter:
    @injector.inject
    def __init__(self, constants: _Constants, config: _Config, injector: injector.Injector, app_state: state.AppState):
        self._constants = constants
        self._config = config
        self._injector = injector
        self._app_state = app_state

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
        self.screen_capture(exact=True)

    def screen_capture(self, exact):
        if not self._app_state.league_enchants.enabled and not self._app_state.daily_enchants.enabled:
            self.show(keys.ErrorWindowKey('No enchant scrapes are enabled, please edit the settings.'))
            return

        save_path = None
        if self._constants.debug:
            save_path = self._constants.screenshots_dir / datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            save_path.mkdir(exist_ok=True)
        curr_enchants = ocr.read_enchants(self._config.ocr.bounds, save_path)

        results = []
        # TODO: make this work for gloves/boots?
        for index, enchant in enumerate(curr_enchants[2:], start=1):
            if not exact:
                enchant = enchants.unexact_mod(enchant)

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

            if league_matches or daily_matches:
                result = _Result(title=enchant, search=f'{enchant} (Helm {index})', league_result=league_matches, daily_result=daily_matches)
                results.append(result)

        if results:
            self.show(keys.SearchWindowKey(results, clear=self._config.ocr.clear_previous))

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

    def delete(self, key):
        logger.debug(f'deleting {key=}')
        self.presenters.pop(key, None)

    def launch(self):
        self.show(keys.SystemTrayIconKey())
        self.show(keys.SearchWindowKey())

    def foreground(self):
        self.show(keys.SearchWindowKey())


from labbie.ui import keys  # noqa: E402
