import loguru
from qtpy import QtCore

from labbie.ui import base
from labbie.ui import utils
from labbie.ui.main.widget import view as search_widget

logger = loguru.logger


class MainWindow(base.BaseWindow):

    def __init__(self, widget: search_widget.MainWidget):
        super().__init__(widget=widget)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self._position_path = None

        utils.register_exit_handler(self._at_exit)

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

    def get_position(self):
        pos = self.pos()
        return pos.x(), pos.y()

    def set_position(self, position):
        if not position:
            self.center_on_screen()
        else:
            self.move(*position)

    def set_position_path(self, path):
        self._position_path = path

    def _at_exit(self):
        if self._position_path:
            with self._position_path.open('w', encoding='utf8') as f:
                x, y = self.get_position()
                logger.debug(f'Saving main window position {x=} {y=}')
                f.write(f'{x} {y}')

    # NOTE: If we want to add minimize button back, this makes it act like close
    # ref: https://stackoverflow.com/questions/16036336/how-to-change-minimize-event-behavior-in-pyqt-or-pyside

    # def changeEvent(self, event):
    #     if event.type() == QtCore.QEvent.WindowStateChange:
    #         if self.windowState() & QtCore.Qt.WindowMinimized:
    #             event.ignore()
    #             self.close()
    #             return

    #     super().changeEvent(event)
