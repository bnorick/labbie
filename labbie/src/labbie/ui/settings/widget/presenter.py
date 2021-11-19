import asyncio

import injector
import loguru

from labbie import config
from labbie import constants
from labbie import state
from labbie.ui import keys
from labbie.ui.app import presenter as app
from labbie.ui.settings.widget import view
from labbie.ui.screen_selection.widget import view as screen_selection

logger = loguru.logger
_Config = config.Config
_Constants = constants.Constants


class SettingsPresenter:

    @injector.inject
    def __init__(
        self,
        constants: _Constants,
        app_state: state.AppState,
        app_presenter: app.AppPresenter,
        config: _Config,
        view: view.SettingsWidget,
        screen_selection_view_builder: injector.AssistedBuilder[screen_selection.ScreenSelectionWidget]
    ):
        self._constants = constants
        self._app_state = app_state
        self._app_presenter = app_presenter
        self._config = config
        self._view = view
        self._screen_selection_view_builder = screen_selection_view_builder
        self._screen_selection_view = None

        self._view.set_select_bounds_handler(self.on_select_bounds)
        self._view.set_reset_window_positions_handler(self.on_reset_window_positions)
        self._view.set_save_handler(self.on_save)

        self._view.league = self._config.league
        self._view.daily = self._config.daily
        self._view.clear_previous = self._config.ocr.clear_previous
        self._view.hotkey = self._config.ui.hotkeys.ocr
        self._view.left = str(self._config.ocr.bounds.left)
        self._view.top = str(self._config.ocr.bounds.top)
        self._view.right = str(self._config.ocr.bounds.right)
        self._view.bottom = str(self._config.ocr.bounds.bottom)

    @property
    def widget(self):
        return self._view

    def on_reset_window_positions(self):
        self._app_presenter.reset_window_positions()

    def on_select_bounds(self, checked):
        if self._screen_selection_view is None:
            self._screen_selection_view = self._screen_selection_view_builder.build(
                left=int(self._view.left),
                top=int(self._view.top),
                right=int(self._view.right),
                bottom=int(self._view.bottom)
            )
            self._screen_selection_view.set_done_handler(self.on_screen_selection_done)
            self._screen_selection_view.show()
            self._view.set_select_button_text('Set')
        else:
            self.on_screen_selection_done()

    def on_screen_selection_done(self):
        left, top, right, bottom = self._screen_selection_view.get_position()
        self._screen_selection_view.hide()
        self._screen_selection_view = None
        self._view.set_select_button_text('Select')
        self._view.left = str(left)
        self._view.top = str(top)
        # TODO(bnorick): identify and fix the underlying bug instead of + 1 as a bandaid fix
        self._view.right = str(right + 1)
        self._view.bottom = str(bottom + 1)

    async def on_save(self):
        try:
            left = int(self._view.left)
            top = int(self._view.top)
            right = int(self._view.right)
            bottom = int(self._view.bottom)

            if right <= left:
                raise ValueError('Left must be less than right')

            if bottom <= top:
                raise ValueError('Top must be less than bottom')
        except ValueError as e:
            err = str(e)
            if err.startswith('invalid literal'):
                e = ValueError('Bounds values (left, top, right, bottom) must be integers')

            self._app_presenter.show(keys.ErrorWindowKey(e))
            return

        if self._view.league != self._config.league:
            self._config.league = self._view.league
            if self._config.league:
                asyncio.create_task(self._app_state.league_enchants.download_or_load(self._constants))
            else:
                self._app_state.league_enchants.set_enchants(None, None)

        if self._view.daily != self._config.daily:
            self._config.daily = self._view.daily
            if self._config.daily:
                asyncio.create_task(self._app_state.daily_enchants.download_or_load(self._constants))
            else:
                self._app_state.daily_enchants.set_enchants(None, None)

        if self._view.hotkey != self._config.ui.hotkeys.ocr:
            self._config.ui.hotkeys.ocr = self._view.hotkey
            self._config.ui.hotkeys.notify(ocr=self._view.hotkey)
        self._config.ocr.clear_previous = self._view.clear_previous
        self._config.ocr.bounds.left = int(self._view.left)
        self._config.ocr.bounds.top = int(self._view.top)
        self._config.ocr.bounds.right = int(self._view.right)
        self._config.ocr.bounds.bottom = int(self._view.bottom)
        self._config.save()
        self._view.close()

    def cleanup(self):
        if self._screen_selection_view:
            self._screen_selection_view.close()

    def show(self):
        self._view.show()
