import os

from PyQt5 import QtCore

from labbie.ui import base
from labbie.ui.about.widget import view as about_widget


class AboutWindow(base.BaseWindow):

    def __init__(self, widget: about_widget.AboutWidget):
        super().__init__(widget=widget)
        self.set_buttons(close=True)
        flags = self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
        if os.name == 'posix':
            flags = flags | QtCore.Qt.Tool
        self.setWindowFlags(flags)
