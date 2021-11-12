import inspect

import loguru
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import qasync

from labbie.vendor.qtmodern import windows

logger = loguru.logger
Qt = QtCore.Qt


class BaseWindow(windows.ModernWindow):
    def __init__(self,
                 widget: QtWidgets.QWidget,
                 window_flags=(Qt.Window
                               | Qt.FramelessWindowHint
                               | Qt.WindowSystemMenuHint),
                 **kwargs
                 ):
        super().__init__(w=widget, **kwargs)
        self.setWindowFlags(window_flags)

        self.widget = widget
        widget.windowTitleChanged.connect(self._widget_window_title_changed)
        if signal_close := getattr(widget, 'signal_close', None):
            self.signal_close = signal_close

    def _widget_window_title_changed(self, title):
        self.setWindowTitle(title)

    def set_buttons(self, minimize=None, maximize=None, close=None):
        kwargs = {}
        if minimize is not None:
            kwargs['minimize'] = minimize
        if maximize is not None:
            kwargs['maximize'] = maximize
        if close is not None:
            kwargs['close'] = close
        self._set_buttons(**kwargs)

    def _set_buttons(self, **kwargs):
        flags = self.windowFlags()

        hints = {
            'minimize': Qt.WindowMinimizeButtonHint,
            'maximize': Qt.WindowMaximizeButtonHint,
            'close': Qt.WindowCloseButtonHint
        }

        for name, value in kwargs.items():
            if hint := hints.get(name):
                if value:
                    flags |= hint
                else:
                    flags &= ~hint
            else:
                raise ValueError(f'Invalid keyword argument "{name}"')

        self.setWindowFlags(flags)

    def show(self):
        super().show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.raise_()
        self.activateWindow()

    def toggle(self):
        if not self.isVisible():
            self.show()
        else:
            self.hide()

    @staticmethod
    def _connect_signal_to_slot(signal, slot):
        if inspect.iscoroutinefunction(slot):
            slot = qasync.asyncSlot()(slot)
        signal.connect(slot)


class BaseWidget(QtWidgets.QWidget):
    signal_close = QtCore.pyqtSignal(name='close')

    def center_on_screen(self, adjust_size=True):
        if adjust_size:
            self.adjustSize()

        # find the topmost window and move it
        last = self
        parent = self.parent()
        while parent:
            last = parent
            parent = parent.parent()

        last.move(QtWidgets.QApplication.instance().desktop().screen().rect().center() - last.rect().center())

    @staticmethod
    def _connect_signal_to_slot(signal, slot):
        if inspect.iscoroutinefunction(slot):
            slot = qasync.asyncSlot()(slot)
        signal.connect(slot)

    def closeEvent(self, event: QtGui.QCloseEvent):
        logger.debug('closeEvent, signalling')
        self.signal_close.emit()
        event.accept()
