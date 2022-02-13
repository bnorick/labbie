import inspect
import os

import injector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
import qasync

Qt = QtCore.Qt
_SIZEGRIP_STYLE = '''
QSizeGrip {
    background-color: rgb(255, 255, 255);
    width: 16px;
    height: 16px;
}
'''


class ScreenSelectionWidget(QtWidgets.QWidget):

    rightClicked = QtCore.Signal()

    @injector.inject
    def __init__(self, left, top, right, bottom, **kwargs):
        super().__init__(**kwargs)
        self.__press_pos = None

        window_flags = Qt.FramelessWindowHint
        if os.name == 'posix':
            window_flags = window_flags | QtCore.Qt.Tool
        self.setWindowFlags(window_flags)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # self.btn_done = QtWidgets.QPushButton('Done', self)
        lbl_done = QtWidgets.QLabel('drag to move\ndrag corners to resize\nright click to set', self)
        lbl_done.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
        lbl_done.setStyleSheet('QLabel { color: rgb(37, 37, 37);}')
        lbl_done.setAlignment(Qt.AlignmentFlag.AlignHCenter)


        def make_sizegrip():
            sizegrip = QtWidgets.QSizeGrip(self)
            sizegrip.setStyleSheet(_SIZEGRIP_STYLE)
            sizegrip.setMinimumSize(16, 16)
            return sizegrip

        sizegrips = [make_sizegrip() for _ in range(4)]

        top_handles = QtWidgets.QHBoxLayout()
        top_handles.setContentsMargins(0, 0, 0, 0)
        top_handles.addWidget(sizegrips[0])
        top_handles.addStretch(1)
        top_handles.addWidget(sizegrips[1])

        bottom_handles = QtWidgets.QHBoxLayout()
        bottom_handles.setContentsMargins(0, 0, 0, 0)
        bottom_handles.addWidget(sizegrips[2])
        bottom_handles.addStretch(1)
        bottom_handles.addWidget(sizegrips[3])

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top_handles)
        layout.addStretch(1)
        layout.addWidget(lbl_done, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        layout.addLayout(bottom_handles)
        self.setLayout(layout)

        self.set_position(left, top, right, bottom)
        self.setMinimumSize(50, 50)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.__press_pos = event.pos()  # remember starting position
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.__press_pos = None

    def mouseMoveEvent(self, event):
        if self.__press_pos:  # follow the mouse
            self.move(self.pos() + (event.pos() - self.__press_pos))

    def paintEvent(self, event=None):
        painter = QtGui.QPainter(self)
        painter.setOpacity(0.7)
        painter.setBrush(Qt.white)
        painter.setPen(QtGui.QPen(Qt.white))
        painter.drawRect(self.rect())

    def set_position(self, left, top, right, bottom):
        self.resize(right - left, bottom - top)
        self.move(left, top)
        self._old_pos = self.pos()

    def get_position(self):
        geom = self.geometry()
        return (geom.left(), geom.top(), geom.right(), geom.bottom())

    def set_done_handler(self, handler):
        self._connect_signal_to_slot(self.rightClicked, handler)

    @staticmethod
    def _connect_signal_to_slot(signal, slot):
        if inspect.iscoroutinefunction(slot):
            slot = qasync.asyncSlot()(slot)
        signal.connect(slot)
