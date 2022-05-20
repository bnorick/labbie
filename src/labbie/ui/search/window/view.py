import os

from PyQt5 import QtCore

from labbie.ui import base
from labbie.ui.search.widget import view as search_widget


class SearchWindow(base.BaseWindow):

    def __init__(self, widget: search_widget.SearchWidget):
        super().__init__(widget=widget)
        self.set_buttons(minimize=False, close=True)

        flags = self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
        if os.name == 'nt':
            flags = flags | QtCore.Qt.SubWindow
        elif os.name == 'posix':
            flags = flags | QtCore.Qt.Tool
        self.setWindowFlags(flags)

    # NOTE: If we want to add minimize button back, this makes it act like close
    # ref: https://stackoverflow.com/questions/16036336/how-to-change-minimize-event-behavior-in-pyqt-or-pyside

    # def changeEvent(self, event):
    #     if event.type() == QtCore.QEvent.WindowStateChange:
    #         if self.windowState() & QtCore.Qt.WindowMinimized:
    #             event.ignore()
    #             self.close()
    #             return

    #     super().changeEvent(event)
