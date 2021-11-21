from qtpy import QtCore

from labbie.ui import base
from labbie.ui.main.widget import view as search_widget


class MainWindow(base.BaseWindow):

    def __init__(self, widget: search_widget.MainWidget):
        super().__init__(widget=widget)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

    def set_taskbar_visibility(self, visible: bool):
        window_was_visible = self.isVisible()
        if visible:
            self.set_buttons(minimize=True, close=True)
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.Tool)
        else:
            self.set_buttons(minimize=False, close=True)
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        if window_was_visible:
            self.show()

    # NOTE: If we want to add minimize button back, this makes it act like close
    # ref: https://stackoverflow.com/questions/16036336/how-to-change-minimize-event-behavior-in-pyqt-or-pyside

    # def changeEvent(self, event):
    #     if event.type() == QtCore.QEvent.WindowStateChange:
    #         if self.windowState() & QtCore.Qt.WindowMinimized:
    #             event.ignore()
    #             self.close()
    #             return

    #     super().changeEvent(event)
