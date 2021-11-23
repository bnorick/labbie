import asyncio

import injector
import loguru

from labbie import config
from labbie import constants
from labbie import state
from labbie import utils
from labbie.ui import keys
from labbie.ui.app import presenter as app
from labbie.ui.settings.widget import view
from labbie.ui.screen_selection.widget import view as screen_selection
from labbie.ui.update import presenter as update

logger = loguru.logger
_Config = config.Config
_Constants = constants.Constants


class SettingsPresenter:

    @injector.inject
    def __init__(
        self,
        config: _Config,
        constants: _Constants,
        app_state: state.AppState,
        app_presenter: app.AppPresenter,
        view: view.SettingsWidget,
        screen_selection_view_builder: injector.AssistedBuilder[screen_selection.ScreenSelectionWidget],
        update_presenter_builder: injector.AssistedBuilder[update.UpdatePresenter]
    ):
        self._config = config
        self._constants = constants
        self._app_state = app_state
        self._app_presenter = app_presenter
        self._view = view
        self._screen_selection_view_builder = screen_selection_view_builder
        self._update_presenter_builder = update_presenter_builder

        self._screen_selection_view = None

        self._view.set_select_bounds_handler(self.on_select_bounds)
        self._view.set_reset_window_positions_handler(self.on_reset_window_positions)
        self._view.set_check_for_update_handler(self.on_check_for_update)
        self._view.set_save_handler(self.on_save)

        self._view.league = self._config.league
        self._view.daily = self._config.daily
        self._view.show_on_taskbar = self._config.ui.show_on_taskbar
        self._view.hotkey = self._config.ui.hotkeys.ocr or ''
        self._view.clear_previous = self._config.ocr.clear_previous
        self._view.left = str(self._config.ocr.bounds.left)
        self._view.top = str(self._config.ocr.bounds.top)
        self._view.right = str(self._config.ocr.bounds.right)
        self._view.bottom = str(self._config.ocr.bounds.bottom)
        self._view.auto_update = self._config.updates.auto_update
        self._view.install_prereleases = self._config.updates.install_prereleases

    @property
    def widget(self):
        return self._view

    def on_reset_window_positions(self):
        self._app_presenter.reset_window_positions()

    async def on_check_for_update(self):
        if not utils.is_frozen():
            logger.info('Update checks are disabled when application is not frozen')
            return
        release_type = 'release' if not self._view.install_prereleases else 'prerelease'
        update_version = await utils.check_for_update(release_type)
        update_presenter = self._update_presenter_builder.build()
        if update_version:
            should_update = await update_presenter.should_update(update_version, release_type)
            if should_update:
                updates_config = self._config.updates
                auto_update = self._view.auto_update
                install_prereleases = self._view.install_prereleases

                changed = False
                if updates_config.auto_update != auto_update:
                    changed = True
                    updates_config.auto_update = auto_update

                if updates_config.install_prereleases != install_prereleases:
                    changed = True
                    updates_config.install_prereleases = install_prereleases

                if changed:
                    self._config.save()
                utils.exit_and_launch_updater(release_type)
        else:
            update_presenter.no_update_available(release_type)

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
        if self._screen_selection_view is not None:
            self.on_screen_selection_done()

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

        # General settings
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

        # UI settings
        show_on_taskbar = self._view.show_on_taskbar
        logger.debug(f'{show_on_taskbar=} {self._config.ui.show_on_taskbar=}')
        if show_on_taskbar != self._config.ui.show_on_taskbar:
            self._config.ui.show_on_taskbar = show_on_taskbar
            self._config.ui.notify(show_on_taskbar=show_on_taskbar)

        # Screen capture settings
        if self._view.hotkey != self._config.ui.hotkeys.ocr:
            self._config.ui.hotkeys.ocr = self._view.hotkey
            self._config.ui.hotkeys.notify(ocr=self._view.hotkey)
        self._config.ocr.clear_previous = self._view.clear_previous
        self._config.ocr.bounds.left = left
        self._config.ocr.bounds.top = top
        self._config.ocr.bounds.right = right
        self._config.ocr.bounds.bottom = bottom

        # Updates settings
        self._config.updates.auto_update = self._view.auto_update
        self._config.updates.install_prereleases = self._view.install_prereleases

        self._config.save()
        self._view.close()

    def cleanup(self):
        if self._screen_selection_view:
            self._screen_selection_view.close()

    def show(self):
        self._view.show()
