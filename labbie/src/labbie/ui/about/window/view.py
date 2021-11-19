from qtpy import QtCore

from labbie.ui import base
from labbie.ui.about.widget import view as about_widget


class AboutWindow(base.BaseWindow):

    def __init__(self, widget: about_widget.AboutWidget):
        super().__init__(widget=widget)
        self.set_buttons(close=True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
