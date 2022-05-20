import os

from PyQt5 import QtCore

from labbie.ui import base
from labbie.ui.settings.widget import view as settings_widget


class SettingsWindow(base.BaseWindow):

    def __init__(self, widget: settings_widget.SettingsWidget):
        super().__init__(widget=widget)
        self.set_buttons(minimize=True, close=True)

        flags = self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
        if os.name == 'posix':
            flags = flags | QtCore.Qt.Tool
        self.setWindowFlags(flags)
