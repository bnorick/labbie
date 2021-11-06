from PyQt5 import QtCore

from labbie.ui import base
from labbie.ui.error.widget import view as error_widget


class ErrorWindow(base.BaseWindow):

    def __init__(self, widget: error_widget.ErrorWidget):
        super().__init__(widget=widget)
        self.set_buttons(close=True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
