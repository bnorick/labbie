import sys

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets


class VTabBar(QtWidgets.QTabBar):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        return

    def tabSizeHint(self, index: int) -> QtCore.QSize:
        s = super().tabSizeHint(index)
        s.transpose()
        return s

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()
        return


class VTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setTabBar(VTabBar())
        self.setTabPosition(QtWidgets.QTabWidget.West)
        return
