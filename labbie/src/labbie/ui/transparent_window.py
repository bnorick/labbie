import inspect

import injector
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import qasync

Qt = QtCore.Qt


class TransparentWindow(QtWidgets.QWidget):

    @injector.inject
    def __init__(self, close_on_click: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._close_on_click = close_on_click

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def mousePressEvent(self, event):
        if self._close_on_click:
            event.ignore()
            self.close()

    def paintEvent(self, event=None):
        painter = QtGui.QPainter(self)
        painter.setOpacity(0.7)
        painter.setBrush(Qt.white)
        painter.setPen(QtGui.QPen(Qt.white))
        painter.drawRect(self.rect())

    @staticmethod
    def _connect_signal_to_slot(signal, slot):
        if inspect.iscoroutinefunction(slot):
            slot = qasync.asyncSlot()(slot)
        signal.connect(slot)
