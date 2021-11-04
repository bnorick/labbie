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

        self._hotkeys: Dict[str, hotkey.Hotkey] = {}
        self._config.ui.hotkeys.attach(self, self._ocr_hotkey_changed, to='ocr')
        self._ocr_hotkey_changed(self._config.ui.hotkeys.ocr)

        self.presenters = {}

    def _ocr_hotkey_changed(self, val):
        current_hotkey = self._hotkeys.pop('ocr', None)
        if current_hotkey:
            current_hotkey.stop()

        if val:
            self._hotkeys['ocr'] = hotkey.Hotkey(val)
            self._hotkeys['ocr'].start(self._ocr_hotkey_pressed)

    def _ocr_hotkey_pressed(self):
        self.screen_capture(True)

    def screen_capture(self, exact):
        save_path = self._constants.data_dir / 'screenshots'
        curr_enchants = ocr.read_enchants(self._config.ocr.bounds, save_path)

        results = []
        # TODO: make this work for gloves/boots?
        for index, enchant in enumerate(curr_enchants[2:], start=1):
            if not exact:
                enchant = enchants.unexact_mod(enchant)

            league_matches = None
            try:
                league_matches = self._app_state.league_enchants.find_matching_enchants(enchant)
            except errors.EnchantsNotLoaded:
                pass

            daily_matches = None
            try:
                daily_matches = self._app_state.daily_enchants.find_matching_enchants(enchant)
            except errors.EnchantsNotLoaded:
                pass

            result = _Result(title=enchant, search=f'{enchant} (Helm {index})', league_result=league_matches, daily_result=daily_matches)
            results.append(result)

        self.show(keys.SearchWindowKey(results))

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


from labbie.ui import keys  # noqa: E402