import os

import injector
import loguru

from labbie import constants
from labbie import utils
from labbie.ui.about.widget import view

logger = loguru.logger
_Constants = constants.Constants


class AboutPresenter:

    @injector.inject
    def __init__(
        self,
        constants: _Constants,
        view: view.AboutWidget
    ):
        self._constants = constants
        self._view = view

        alternate_mode = 'normal' if constants.debug else 'debug'
        self._view.set_relauch_text(f'Relaunch in {alternate_mode} mode')

        self._view.set_relaunch_handler(self.on_relaunch)
        self._view.set_open_data_handler(self.on_open_data)
        self._view.set_open_logs_handler(self.on_open_logs)

    @property
    def widget(self):
        return self._view

    def cleanup(self):
        pass

    def show(self):
        self._view.show()

    def on_relaunch(self, checked):
        utils.relaunch(debug=not self._constants.debug, exit_fn=lambda: self._view.exit())

    def on_open_data(self, checked):
        if self._constants.data_dir.is_dir():
            os.startfile(self._constants.data_dir)

    def on_open_logs(self, checked):
        if self._constants.logs_dir.is_dir():
            os.startfile(self._constants.logs_dir)
