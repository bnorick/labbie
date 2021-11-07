import inspect

import qasync
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from labbie.ui import utils as utils


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        icon_path = utils.asset_path('taxi.png')
        self.setIcon(QtGui.QIcon(str(icon_path)))
        self.menu = QtWidgets.QMenu()

        self.action_search = self.menu.addAction('Search')
        self.action_settings = self.menu.addAction('Settings')
        self.action_about = self.menu.addAction('About')
        action_exit = self.menu.addAction('Exit')
        action_exit.triggered.connect(self.exit)
        self.setContextMenu(self.menu)

    def exit(self):
        QtWidgets.QApplication.exit()

    def set_search_triggered_handler(self, handler):
        self._connect_signal_to_slot(self.action_search.triggered, handler)

    def set_settings_triggered_handler(self, handler):
        self._connect_signal_to_slot(self.action_settings.triggered, handler)

    def set_about_triggered_handler(self, handler):
        self._connect_signal_to_slot(self.action_about.triggered, handler)

    @staticmethod
    def _connect_signal_to_slot(signal, slot):
        if inspect.iscoroutinefunction(slot):
            slot = qasync.asyncSlot()(slot)
        signal.connect(slot)
