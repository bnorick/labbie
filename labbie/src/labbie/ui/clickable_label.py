from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets


class ClickableLabel(QtWidgets.QLabel):

    clicked = QtCore.Signal()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.clicked.emit()
