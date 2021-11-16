from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets


class ClickableLabel(QtWidgets.QLabel):

    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.clicked.emit()
