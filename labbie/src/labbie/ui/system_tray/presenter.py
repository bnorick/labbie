import atexit

import injector

from labbie.ui import keys
from labbie.ui.app import presenter as app
from labbie.ui.system_tray import view


class SystemTrayIconPresenter:
    @injector.inject
    def __init__(self, view: view.SystemTrayIcon, app_presenter: app.AppPresenter):
        self._view = view
        self._app_presenter = app_presenter

        self._view.set_double_click_handler(self.on_search_triggered)
        self._view.set_search_triggered_handler(self.on_search_triggered)
        self._view.set_settings_triggered_handler(self.on_settings_triggered)
        self._view.set_about_triggered_handler(self.on_about_triggered)

        atexit.register(self._at_exit)

    def show(self):
        self._view.show()

    def _at_exit(self):
        try:
            self._view.hide()
        except RuntimeError:
            pass

    def on_search_triggered(self):
        self._app_presenter.show(keys.SearchWindowKey())

    def on_settings_triggered(self):
        self._app_presenter.show(keys.SettingsWindowKey())

    def on_about_triggered(self):
        self._app_presenter.show(keys.AboutWindowKey())
