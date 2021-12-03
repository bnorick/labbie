from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

from labbie.ui import base
from labbie.ui import utils

_BUTTON_ICON_SPACING = 0.5  # 50%


# class Delegate(QtWidgets.QStyledItemDelegate):
#     def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
#         return super().paint(painter, option, index)


# class MyItem(QtGui.QStandardItem):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.


# class ElidedLabel(QtWidgets.QLabel):

#     elision_changed = QtCore.Signal(bool)

#     def __init__(self, text='', parent=None, mode=QtCore.Qt.ElideRight, **kwargs):
#         super().__init__(parent=parent, **kwargs)

#         self._mode = mode
#         self.elided = False

#         self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
#         self.setText(text)

#     def setText(self, text):
#         self._contents = text
#         # Changing the content require a repaint of the widget (or so
#         # says the overview)
#         self.update()

#     def text(self):
#         return self._contents

#     def minimumSizeHint(self):
#         metrics = QtGui.QFontMetrics(self.font())
#         return QtCore.QSize(0, metrics.height())

#     def paintEvent(self, event):

#         super().paintEvent(event)

#         did_elide = False

#         painter = QtGui.QPainter(self)
#         font_metrics = painter.fontMetrics()
#         # fontMetrics.width() is deprecated; use horizontalAdvance
#         text_width = font_metrics.horizontalAdvance(self.text())

#         # Layout phase, per the docs
#         text_layout = QtGui.QTextLayout(self._contents, painter.font())
#         text_layout.beginLayout()

#         # while True:

#         #     line = text_layout.createLine()

#         #     if not line.isValid():
#         #         break

#         #     line.setLineWidth(self.width())

#         #     print(f'{line.naturalTextWidth()=} {self.width()=} {line=}')

#         y = 0
#         line_spacing = font_metrics.lineSpacing()

#         for line_text in self._contents.splitlines():
#             next_y = y + line_spacing
#             print(f'LINE TEXT {line_text} {type(line_text)=}')
#             try:
#             # if line.naturalTextWidth() >= self.width():
#                 elided_line = font_metrics.elidedText(line_text, self._mode, self.width())
#                 print(f'ELIDED {elided_line}')
#                 painter.drawText(QtCore.QPoint(0, y + font_metrics.ascent()), elided_line)
#                 # did_elide |= line.isValid()
#                 # break
#             except TypeError:
#                 print(f'{line_text=} {self._mode=} {self.width()=}')
#             y = next_y
#             # else:
#             #     line.draw(painter, QtCore.QPoint(0, 0))

#         # text_layout.endLayout()

#         self.elision_changed.emit(did_elide)

#         if did_elide != self.elided:
#             self.elided = did_elide
#             self.elision_changed.emit(did_elide)


class TestLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f'{id(self)} -> {self.text()}')

    def setText(self, arg__1: str) -> None:
        print(f'{id(self)} -> {self.text()}')
        return super().setText(arg__1)

    def updateGeometry(self) -> None:
        print(f'UPDATE GEOMETRY {id(self)}')
        return super().updateGeometry()


class ElidedLabel(QtWidgets.QLabel):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     print(f'{id(self)} -> {self.text()}')

    # def setText(self, arg__1: str) -> None:
    #     print(f'{id(self)} -> {self.text()}')
    #     return super().setText(arg__1)

    # def adjustSize(self) -> None:
    #     print(f'ADJUST SIZE {id(self)}')
    #     return super().adjustSize()

    # def updateGeometry(self) -> None:
    #     print(f'UPDATE GEOMETRY {id(self)}')
    #     return super().updateGeometry()

    # def setMinimumSize(self, minw: int, minh: int) -> None:
    #     print(f'SET MIN SIZE {id(self)}')
    #     return super().setMinimumSize(minw, minh)

    # def setMinimumWidth(self, minw: int) -> None:
    #     print(f'SET MIN WIDTH {id(self)}')
    #     return super().setMinimumWidth(minw)

    # def setFixedWidth(self, w: int) -> None:
    #     print(f'SET FIXED WIDTH {id(self)}')
    #     return super().setFixedWidth(w)

    def sizeHint(self):
        return QtCore.QSize(-1, super().sizeHint().height())

    def minimumSizeHint(self):
        return QtCore.QSize(-1, super().minimumSizeHint().height())

    def paintEvent(self, event):
        # print(f'PAINT {id(self)} {self.width()=} {self.parent().width()=}')
        painter = QtGui.QPainter(self)
        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)


class ListItem(QtWidgets.QWidget):
    def __init__(self, count: int, name: str, parent=None):
        super().__init__(parent=parent)

        # palette = QtGui.QPalette()
        # palette.setColor(QtGui.QPalette.Base, QtGui.QColor('red'))
        # self.setPalette(palette)
        # self.setAutoFillBackground(True)

        self.setMouseTracking(True)

        count_size = (43, 43)

        lbl_count = QtWidgets.QLabel(str(count), self)
        lbl_count.setStyleSheet('QLabel { font-size: 17pt; font-family: Arial; background: palette(base); } '
                                'QLabel[selected="true"] { background: palette(highlight); }')
        lbl_count.setFixedSize(*count_size)
        lbl_count.adjustSize()

        stylesheet_btn = 'QPushButton { border: none; background: palette(button); padding: 3px; } QPushButton:hover { border: 1px solid palette(light); background: palette(midlight); }'
        btn_minus = QtWidgets.QPushButton(utils.icon('minus.svg', 180), '', lbl_count)
        btn_plus = QtWidgets.QPushButton(utils.icon('plus.svg', 180), '', lbl_count)
        btn_minus.setStyleSheet(stylesheet_btn)
        btn_plus.setStyleSheet(stylesheet_btn)
        w, h = btn_plus.iconSize().toTuple()
        btn_minus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_minus.setFixedSize(21, 19)
        btn_minus.move(lbl_count.rect().bottomLeft() - btn_minus.rect().bottomLeft())
        btn_plus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_plus.setFixedSize(21, 19)
        btn_plus.move(lbl_count.rect().bottomRight() - btn_plus.rect().bottomRight())

        lbl_name = ElidedLabel(name, self)
        lbl_name.setStyleSheet('QLabel { font-size: 10pt; }')
        lbl_name.setFixedHeight(count_size[1])

        # TODO(bnorick): add ilvl/inf and vaal orb icon (with hover details) for corrupts

        # lbl_count.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # lbl_name.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # lbl_name.adjustSize()

        print(f'{lbl_count.sizeHint()=}\n{lbl_name.sizeHint()=}\n{self.sizeHint()=}')

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(lbl_count)
        layout.addSpacing(5)
        layout.addWidget(lbl_name)
        # layout.addSpacing(20)
        print(self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent))
        # layout.addSpacing(self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent) + 2 + 12)
        # layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.setLayout(layout)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        print(f'PRE ADJUST\n  {lbl_count.sizeHint()=}\n  {lbl_name.sizeHint()=}\n  {self.sizeHint()=}\n  {self.size()=}')
        self.adjustSize()
        print(f'POST ADJUST\n  {lbl_count.sizeHint()=}\n  {lbl_name.sizeHint()=}\n  {self.sizeHint()=}\n  {self.size()=}')

        btn_config = QtWidgets.QPushButton(utils.icon('config.svg', 180), '', lbl_name)
        btn_config.setStyleSheet(stylesheet_btn)
        btn_config.setFixedSize(21, 19)
        # btn_config.move(self.rect().bottomRight() - btn_config.rect().bottomRight())

        self.lbl_count = lbl_count
        self.lbl_name = lbl_name
        self.btn_minus = btn_minus
        self.btn_plus = btn_plus
        self.btn_config = btn_config

        self.lbl_count.setAlignment(QtCore.Qt.AlignCenter)
        # self.lbl_name.setAlignment(QtCore.Qt.AlignTop)

        self.on_hover(False)

    # def paintEvent(self, pe):
    #     opt = QtWidgets.QStyleOption()
    #     opt.init(self)
    #     p = QtGui.QPainter(self)
    #     s = self.style()
    #     s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)

    def resizeEvent(self, event):
        self.btn_config.move(self.lbl_name.rect().bottomRight() - self.btn_config.rect().bottomRight())
        return super().resizeEvent(event)

    def enterEvent(self, event):
        self.on_hover(True)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.on_hover(False)
        return super().leaveEvent(event)

    def on_hover(self, hovered: bool):
        # if hovered:
        #     self.lbl_count.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        #     self.lbl_name.setAlignment(QtCore.Qt.AlignTop)
        # else:
        #     self.lbl_count.setAlignment(QtCore.Qt.AlignCenter)
        #     self.lbl_name.setAlignment(QtCore.Qt.AlignVCenter)

        self.btn_minus.setVisible(hovered)
        self.btn_plus.setVisible(hovered)
        self.btn_config.setVisible(hovered)

    def on_selection(self, selected: bool):
        self.lbl_count.setProperty('selected', str(selected).lower())
        self.lbl_count.style().unpolish(self.lbl_count)
        self.lbl_count.style().polish(self.lbl_count)


class ListItem2(QtWidgets.QWidget):
    def __init__(self, count: int, name: str, ilvl: str = None, inf: str = None, corrupt: str = None, parent=None):
        super().__init__(parent=parent)

        self.setMouseTracking(True)

        # count_size = (43, 43)

        lbl_count = QtWidgets.QLabel(str(count), self)
        lbl_count.setStyleSheet('QLabel { font-size: 10pt; font-family: Arial; }')
        lbl_count.setFixedWidth(25)
        lbl_count.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        # lbl_count.setStyleSheet('QLabel { font-size: 10pt; font-family: Arial; background: palette(base); } '
        #                         'QLabel[selected="true"] { background: palette(highlight); }')
        # lbl_count.setFixedSize(*count_size)
        # lbl_count.adjustSize()

        stylesheet_btn = 'QPushButton { border: none; background: palette(button); padding: 3px; } QPushButton:hover { border: 1px solid palette(light); background: palette(midlight); }'
        btn_minus = QtWidgets.QPushButton(utils.icon('minus.svg', 180), '', self)
        btn_plus = QtWidgets.QPushButton(utils.icon('plus.svg', 180), '', self)
        btn_minus.setStyleSheet(stylesheet_btn)
        btn_plus.setStyleSheet(stylesheet_btn)
        w, h = btn_plus.iconSize().toTuple()
        btn_minus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_minus.setFixedSize(21, 19)
        btn_minus.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # btn_minus.move(0, int(lbl_count.rect().height() / 2) - btn_minus.rect().bottomLeft())
        btn_plus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_plus.setFixedSize(21, 19)
        btn_plus.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # btn_plus.move(lbl_count.rect().bottomRight() - btn_plus.rect().bottomRight())

        layout_text = QtWidgets.QVBoxLayout()
        layout_text.setContentsMargins(0, 0, 0, 0)

        lbl_name = ElidedLabel(name, self)
        lbl_name.setStyleSheet('QLabel { font-size: 10pt; }')
        lbl_name.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout_text.addWidget(lbl_name)
        lbl_name.adjustSize()

        lbl_name_unelided = QtWidgets.QLabel(name, self)
        lbl_name_unelided.setStyleSheet('QLabel { font-size: 10pt; }')
        layout_text.addWidget(lbl_name_unelided)
        lbl_name_unelided.hide()
        lbl_name_unelided.setWordWrap(True)

        info_text = []
        if ilvl is not None:
            info_text.append(f'{ilvl}{" " + inf.title() if inf is not None else ""}')
        # if corrupt is not None:
        if corrupt:
            info_text.append(corrupt)
        lbl_info = None
        if info_text:
            lbl_info = QtWidgets.QLabel(self)
            lbl_info.setWordWrap(True)
            lbl_info.setText('\n'.join(info_text))
            lbl_info.setStyleSheet('QLabel { font-size: 8pt; }')
            lbl_info.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            layout_text.addSpacing(3)
            layout_text.addWidget(lbl_info)
            lbl_info.hide()

        # lbl_name.setFixedHeight(count_size[1])

        # TODO(bnorick): add ilvl/inf and vaal orb icon (with hover details) for corrupts

        # lbl_count.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # lbl_name.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # lbl_name.adjustSize()

        print(f'{lbl_count.sizeHint()=}\n{lbl_name.sizeHint()=}\n{self.sizeHint()=}')
        btn_config = QtWidgets.QPushButton(utils.icon('config.svg', 180), '', self)
        btn_config.setStyleSheet(stylesheet_btn)
        btn_config.setFixedSize(21, 19)

        size_policy = btn_minus.sizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        btn_minus.setSizePolicy(size_policy)

        size_policy = btn_plus.sizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        btn_plus.setSizePolicy(size_policy)

        layout_count = QtWidgets.QHBoxLayout()
        layout_count.setContentsMargins(0, 0, 0, 0)
        layout_count.addWidget(btn_minus)
        layout_count.addWidget(lbl_count)
        layout_count.addWidget(btn_plus)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addLayout(layout_count, 25)
        layout.addSpacing(5)
        layout.addLayout(layout_text, 75)
        # layout.addWidget(btn_config)
        # layout.addSpacing(20)
        # layout.addSpacing(self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent) + 2 + 12)
        # layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.setLayout(layout)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        print(f'PRE ADJUST\n  {lbl_count.sizeHint()=}\n  {lbl_name.sizeHint()=}\n  {self.sizeHint()=}\n  {self.size()=}')
        self.adjustSize()
        print(f'POST ADJUST\n  {lbl_count.sizeHint()=}\n  {lbl_name.sizeHint()=}\n  {self.sizeHint()=}\n  {self.size()=}')

        self.lbl_count = lbl_count
        self.lbl_name = lbl_name
        self.lbl_name_unelided = lbl_name_unelided
        self.lbl_info = lbl_info
        self.btn_minus = btn_minus
        self.btn_plus = btn_plus
        self.btn_config = btn_config
        self.layout_count = layout_count
        self.layout_text = layout_text

        self.lbl_count.setAlignment(QtCore.Qt.AlignCenter)
        # self.lbl_name.setAlignment(QtCore.Qt.AlignTop)

        self.setStyleSheet('QWidget[selected="false"] { border: 2px solid transparent; } QWidget[selected="true"] { border: 2px solid palette(highlight); }')

        # size = self.sizeHint()
        # size.setHeight(size.height() + 3)
        # self.setMinimumSize(size)

        self.on_hover(False)
        self.on_selection(False)

    def paintEvent(self, pe):
        opt = QtWidgets.QStyleOption()
        opt.init(self)
        p = QtGui.QPainter(self)
        s = self.style()
        s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)

    def resizeEvent(self, event):
        # self.btn_config.move(self.lbl_name.rect().bottomRight() - self.btn_config.rect().bottomRight())
        # print(
        #     f'\nRESIZE\n{self.lbl_info.text()}\n{self.lbl_name.width()=}\n'
        #     f'{self.lbl_info.width()=}\n'
        #     f'{self.layout_count.geometry()=}\n'
        # )

        self.btn_config.move(self.rect().topRight() - self.btn_config.rect().topRight() - QtCore.QPoint(2, -2))
        self.lbl_name.adjustSize()
        self.lbl_name_unelided.setFixedWidth(self.lbl_name.width())
        if self.lbl_info:
            self.lbl_info.setFixedWidth(self.lbl_name.width())
        return super().resizeEvent(event)

    def enterEvent(self, event):
        self.on_hover(True)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.on_hover(False)
        return super().leaveEvent(event)

    def on_hover(self, hovered: bool):
        # if hovered:
        #     self.lbl_count.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        #     self.lbl_name.setAlignment(QtCore.Qt.AlignTop)
        # else:
        #     self.lbl_count.setAlignment(QtCore.Qt.AlignCenter)
        #     self.lbl_name.setAlignment(QtCore.Qt.AlignVCenter)

        # print(
        #     f'\nHOVER\n{self.lbl_name.width()=}\n'
        #     f'{self.lbl_info.width()=}\n'
        #     f'{self.layout_count.geometry()=}\n'
        # )

        self.btn_minus.setVisible(hovered)
        self.btn_plus.setVisible(hovered)
        self.btn_config.setVisible(hovered)

    def on_selection(self, selected: bool):
        self.setProperty('selected', str(selected).lower())
        self.style().unpolish(self)
        self.style().polish(self)

        # print(
        #     f'\nSELECT\n{self.lbl_name.width()=}\n'
        #     f'{self.lbl_info.width()=}\n'
        #     f'{self.layout_count.geometry()=}\n'
        # )

        self.lbl_name.setVisible(not selected)
        self.lbl_name_unelided.setVisible(selected)

        if self.lbl_info:
            self.lbl_info.setVisible(selected)
            print(f'\n{"SHOW" if selected else "HIDE"}\n{self.lbl_info.text()}')
            self.lbl_info.adjustSize()
            # self.lbl_name.updateGeometry()
        # print(
        #     f'\nSELECT\n{self.lbl_name.width()=}\n'
        #     f'{self.lbl_info.width()=}\n'
        #     f'{self.layout_count.geometry()=}\n'
        # )
        self.layout_text.update()
        # self.adjustSize()
        # self.lbl_count.setProperty('selected', str(selected).lower())
        # self.lbl_count.style().unpolish(self.lbl_count)
        # self.lbl_count.style().polish(self.lbl_count)


class BuyListWidget(base.BaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Table of
        # [(dumpster / -) count +]   [Base]
        # in the order they were added
        # Buy button   Cog wheel button
        # Remove button
        #
        # Right click context menu for "Set custom search"
        #   opens a dialog to enter the search slug which should be opened when buying

#         list_view = QtWidgets.QListView(self)
#         list_model = QtGui.QStandardItemModel()

#         list_view.setStyleSheet("""QListView {
#     show-decoration-selected: 1; /* make the selection span the entire width of the view */
# }

# QListView::item:alternate {
#     background: #EEEEEE;
# }

# QListView::item:selected {
#     border: 1px solid #6a6ea9;
# }

# QListView::item:selected:!active {
#     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                 stop: 0 #ABAFE5, stop: 1 #8588B2);
# }

# QListView::item:selected:active {
#     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                 stop: 0 #6a6ea9, stop: 1 #888dd9);
# }

# QListView::item:hover {
#     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                 stop: 0 #FAFBFE, stop: 1 #DCDEF1);
# }""")

#         list_view.setModel(list_model)
#         list_view.setMouseTracking(True)
#         list_view.entered.connect(lambda *args: print(args))

#         list_model.set

#         item1 = QtGui.QStandardItem()
#         item1.
#         list_model.appendRow(item1)



        # Meh...
        # action_margins = (0.35, 0.35, 0.35, 0.35)

        # btn_minus = QtWidgets.QPushButton(utils.recolored_icon('minus.svg', 180), '', self)
        # btn_plus = QtWidgets.QPushButton(utils.recolored_icon('plus.svg', 180), '', self)
        # w, h = btn_plus.iconSize().toTuple()
        # btn_minus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        # btn_plus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))

        # lbl_count = QtWidgets.QLabel('5', self)
        # lbl_name = QtWidgets.QLabel('Royal Burgonet', self)
        # icon_buy = utils.recolored_icon('buy.svg', 180, margins=(None, None, _BUTTON_ICON_SPACING, None))
        # btn_buy = QtWidgets.QPushButton(icon_buy, 'Buy', self)
        # w, h = btn_buy.iconSize().toTuple()
        # btn_buy.setIconSize(QtCore.QSize(round(w * (1 + _BUTTON_ICON_SPACING)), h))
        # btn_done = QtWidgets.QPushButton(utils.recolored_icon('tick.svg', 180, margins=action_margins), '', self)
        # btn_config = QtWidgets.QPushButton(utils.recolored_icon('config.svg', 180), '', self)

        # layout_buttons = QtWidgets.QHBoxLayout()
        # layout_buttons.addWidget(btn_buy)
        # layout_buttons.addWidget(btn_done)
        # layout_buttons.addStretch(1)
        # layout_buttons.addWidget(btn_config)

        # layout_buy_list = QtWidgets.QGridLayout()
        # # layout_buy_list.addWidget(btn_buy, 0, 0, 1, 4)
        # # layout_buy_list.addWidget(btn_done, 1, 0, 1, 4)
        # layout_buy_list.addLayout(layout_buttons, 0, 0, 1, 5)

        # layout_buy_list.addWidget(btn_minus, 1, 0)
        # layout_buy_list.addWidget(btn_plus, 1, 1)
        # layout_buy_list.addWidget(lbl_count, 1, 3)
        # layout_buy_list.addWidget(lbl_name, 1, 4)
        # layout_buy_list.setSpacing(0)
        # layout_buy_list.setColumnMinimumWidth(2, 5)

        # buy_list.setStyleSheet('QListView::item[selected="true"] QHBoxLayout { background: palette(base); }')

        # layout_buy_list = QtWidgets.QGridLayout()
        # # layout_buy_list.addWidget(btn_buy, 0, 0, 1, 4)
        # # layout_buy_list.addWidget(btn_done, 1, 0, 1, 4)
        # layout_buy_list.addLayout(layout_buttons, 0, 0, 1, 5)

        # layout_buy_list.addWidget(btn_minus, 1, 0)12345444849555584474457567767112367890
        # layout_buy_list.addWidget(btn_plus, 1, 1)
        # layout_buy_list.addWidget(lbl_count, 1, 3)
        # layout_buy_list.addWidget(lbl_name, 1, 4)
        # layout_buy_list.setSpacing(0)
        # layout_buy_list.setColumnMinimumWidth(2, 5)

        # app_palette = QtWidgets.QApplication.instance().palette()
        # selected_palette = QtGui.QPalette()
        # selected_palette.setColor(QtGui.QPalette.Window, app_palette.highlight().color())
        # selected_palette.setColor(QtGui.QPalette.WindowText, app_palette.highlightedText().color())

        # lbl_count.setPalette(selected_palette)
        # lbl_count.setAutoFillBackground(True)

        # lbl_name.setPalette(selected_palette)
        # lbl_name.setAutoFillBackground(True)

        # btn_minus = QtWidgets.QPushButton(utils.recolored_icon('minus.svg', 180), '', self)
        # btn_plus = QtWidgets.QPushButton(utils.recolored_icon('plus.svg', 180), '', self)
        # lbl_count = QtWidgets.QLabel('5', self)
        # lbl_name = QtWidgets.QLabel('Royal Burgonet', self)
        # btn_buy = QtWidgets.QPushButton(utils.recolored_icon('buy.svg', 180), '', self)
        # btn_done = QtWidgets.QPushButton(utils.recolored_icon('done.svg', 180), '', self)
        # btn_trash = QtWidgets.QPushButton(utils.recolored_icon('trash.svg', 180), '', self)
        # layout_buy_list = QtWidgets.QGridLayout()
        # layout_buy_list.addWidget(btn_minus, 0, 0)
        # layout_buy_list.addWidget(btn_plus, 0, 1)
        # layout_buy_list.addWidget(lbl_count, 0, 2)
        # layout_buy_list.addWidget(lbl_name, 0, 3)
        # layout_buy_list.addWidget(btn_buy, 0, 4)
        # layout_buy_list.addWidget(btn_done, 0, 5)
        # layout_buy_list.addWidget(btn_trash, 0, 6)

        # table = QtWidgets.QTableWidget(0, 7, self)
        # table.insertRow(0)

        # btn_minus = QtWidgets.QPushButton(utils.recolored_icon('minus.svg', 180), '', self)
        # btn_plus = QtWidgets.QPushButton(utils.recolored_icon('plus.svg', 180), '', self)
        # table.setCellWidget(0, 0, btn_minus)
        # table.setCellWidget(0, 1, btn_plus)
        # table.setItem(0, 2, QtWidgets.QTableWidgetItem('5'))
        # table.setItem(0, 3, QtWidgets.QTableWidgetItem('Royal Burgonet'))
        # btn_buy = QtWidgets.QPushButton(utils.recolored_icon('buy.svg', 180), '', self)
        # btn_done = QtWidgets.QPushButton(utils.recolored_icon('done.svg', 180), '', self)
        # btn_trash = QtWidgets.QPushButton(utils.recolored_icon('trash.svg', 180), '', self)
        # table.setCellWidget(0, 4, btn_buy)
        # table.setCellWidget(0, 5, btn_done)
        # table.setCellWidget(0, 6, btn_trash)

        # table.resizeColumnsToContents()
        # table.resizeRowsToContents()

        # btn_config = QtWidgets.QPushButton(utils.recolored_icon('config.svg', 180), '', self)

        # layout_buttons = QtWidgets.QHBoxLayout()
        # layout_buttons.addWidget(btn_buy)
        # layout_buttons.addWidget(btn_done)
        # layout_buttons.addWidget(btn_trash)
        # layout_buttons.addWidget(btn_config)
        # layout_buttons.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)

        # layout = QtWidgets.QVBoxLayout()
        # layout.addLayout(layout_buttons)
        # layout.addWidget(buy_list)
        # # layout.addWidget(list_view)
        # # layout.addLayout(layout_buy_list)
        # # layout.addWidget(table)
        # # layout.addStretch(1)
        # # layout.addLayout(layout_buttons)

        # self.setLayout(layout)
        self._init_ui()

    def _init_ui1(self):
        btn_minus = QtWidgets.QPushButton(utils.icon('minus.svg', 180), '', self)
        btn_plus = QtWidgets.QPushButton(utils.icon('plus.svg', 180), '', self)
        btn_config = QtWidgets.QPushButton(utils.icon('config.svg', 180), '', self)
        w, h = btn_plus.iconSize().toTuple()
        btn_minus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_plus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        lbl_count = QtWidgets.QLabel('5', self)
        lbl_name = QtWidgets.QLabel('Royal Burgonet', self)

        icon_buy = utils.icon('buy.svg', 180, margins=(None, None, _BUTTON_ICON_SPACING, None))
        btn_buy = QtWidgets.QPushButton(icon_buy, 'Buy', self)
        w, h = btn_buy.iconSize().toTuple()
        btn_buy.setIconSize(QtCore.QSize(round(w * (1 + _BUTTON_ICON_SPACING)), h))
        btn_done = QtWidgets.QPushButton(utils.icon('tick.svg', 180, margins=0.35), '', self)

        layout_buttons = QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(btn_buy)
        layout_buttons.addWidget(btn_done)

        buy_list = QtWidgets.QListWidget(self)

        item1_widget = QtWidgets.QWidget()
        layout_widget = QtWidgets.QGridLayout()
        widget_buttons = QtWidgets.QWidget()
        widget_buttons.setObjectName('buttons')
        layout_widget_buttons = QtWidgets.QHBoxLayout()
        layout_widget_buttons.addWidget(btn_minus)
        layout_widget_buttons.addWidget(btn_plus)
        layout_widget_buttons.addStretch(1)
        layout_widget_buttons.addWidget(btn_config)
        widget_buttons.setLayout(layout_widget_buttons)
        layout_widget.addWidget(lbl_count, 0, 0)
        layout_widget.addWidget(lbl_name, 0, 1)
        layout_widget.addWidget(widget_buttons, 1, 0, 1, 2)
        layout_widget.setContentsMargins(0, 0, 0, 0)
        item1_widget.setLayout(layout_widget)

        item1 = QtWidgets.QListWidgetItem()
        item1.setSizeHint(item1_widget.sizeHint())
        buy_list.addItem(item1)
        buy_list.setItemWidget(item1, item1_widget)
        buy_list.setStyleSheet('QWidget#buttons { background: palette(base); }')

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_buttons)
        layout.addWidget(buy_list)
        self.setLayout(layout)

    def _init_ui2(self):
        icon_buy = utils.icon('buy.svg', 180, margins=(None, None, _BUTTON_ICON_SPACING, None))
        btn_buy = QtWidgets.QPushButton(icon_buy, 'Buy', self)
        w, h = btn_buy.iconSize().toTuple()
        btn_buy.setIconSize(QtCore.QSize(round(w * (1 + _BUTTON_ICON_SPACING)), h))
        btn_done = QtWidgets.QPushButton(utils.icon('tick.svg', 180, margins=0.35), '', self)

        lbl_count = QtWidgets.QLabel('5', self)
        lbl_count.setStyleSheet('QLabel { font-size: 17pt; font-family: Arial; background: palette(highlight); qproperty-alignment: \'AlignTop | AlignHCenter\';  }')
        lbl_count.setFixedSize(43, 43)
        lbl_count.adjustSize()
        # lbl_count.setAlignment(QtCore.Qt.AlignTop)

        stylesheet_btn = 'QPushButton { border: none; background: palette(button); padding: 3px; } QPushButton:hover { border: 1px solid palette(light); background: palette(midlight); }'
        btn_minus = QtWidgets.QPushButton(utils.icon('minus.svg', 180), '', lbl_count)
        btn_plus = QtWidgets.QPushButton(utils.icon('plus.svg', 180), '', lbl_count)
        btn_minus.setStyleSheet(stylesheet_btn)
        btn_plus.setStyleSheet(stylesheet_btn)
        w, h = btn_plus.iconSize().toTuple()
        btn_minus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_minus.setFixedSize(21, 19)
        btn_minus.move(lbl_count.rect().bottomLeft() - btn_minus.rect().bottomLeft())
        btn_plus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_plus.setFixedSize(21, 19)
        btn_plus.move(lbl_count.rect().bottomRight() - btn_plus.rect().bottomRight())

        lbl_name = QtWidgets.QLabel('Royal Burgonet', self)
        lbl_name.setStyleSheet('QLabel { font-size: 10pt; }')
        btn_config = QtWidgets.QPushButton(utils.icon('config.svg', 180), '', self)
        btn_config.setStyleSheet(stylesheet_btn)

        layout_buttons = QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(btn_buy)
        layout_buttons.addWidget(btn_done)

        buy_list = QtWidgets.QListWidget(self)
        buy_list.setSpacing(5)
        buy_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        buy_list.setResizeMode(QtWidgets.QListWidget.Adjust)
        # buy_list.setSizeAdjustPolicy(QtWidgets.QListWidget.AdjustToContents)
        # buy_list.setResizeMode(QtWidgets.QListView.Adjust)
        # buy_list.setMinimumWidth(item1_widget.sizeHint().width())
        # buy_list.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        item1_widget = QtWidgets.QWidget()
        layout_widget = QtWidgets.QGridLayout()
        widget_buttons = QtWidgets.QWidget()
        widget_buttons.setObjectName('buttons')
        layout_widget_buttons = QtWidgets.QHBoxLayout()
        layout_widget_buttons.addWidget(lbl_count)
        layout_widget_buttons.setContentsMargins(0, 0, 0, 0)
        widget_buttons.setLayout(layout_widget_buttons)

        layout_widget.addWidget(widget_buttons, 0, 0, 2, 1)
        layout_widget.addWidget(lbl_name, 0, 1, 1, 2)
        layout_widget.addWidget(btn_config, 1, 2)
        layout_widget.setContentsMargins(0, 0, 0, 0)
        layout_widget.setColumnStretch(1, 1)
        layout_widget.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        item1_widget.setLayout(layout_widget)
        item1_widget.adjustSize()

        print(item1_widget.sizeHint())

        item1 = QtWidgets.QListWidgetItem()
        item1.setSizeHint(item1_widget.sizeHint())
        buy_list.addItem(item1)
        buy_list.setItemWidget(item1, item1_widget)
        # item1.setSizeHint(item1_widget.sizeHint())
        # buy_list.setStyleSheet('QWidget#buttons { background: palette(base); }')
        buy_list.setStyleSheet('QListWidget::item:selected:focus { background: palette(base); }')

        print(item1.sizeHint())
        print(buy_list.width())
        buy_list.adjustSize()

        buy_list.setMinimumWidth(buy_list.sizeHintForColumn(0) + 2 * buy_list.frameWidth() + 2 * buy_list.spacing())
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_buttons)
        layout.addWidget(buy_list)
        print(buy_list.width())
        self.setLayout(layout)
        print(buy_list.width())
        self.buy_list = buy_list


    def _init_ui3(self):
        icon_buy = utils.icon('buy.svg', 180, margins=(None, None, _BUTTON_ICON_SPACING, None))
        btn_buy = QtWidgets.QPushButton(icon_buy, 'Buy', self)
        w, h = btn_buy.iconSize().toTuple()
        btn_buy.setIconSize(QtCore.QSize(round(w * (1 + _BUTTON_ICON_SPACING)), h))
        btn_done = QtWidgets.QPushButton(utils.icon('tick.svg', 180, margins=0.35), '', self)

        count_size = (43, 43)

        lbl_count = QtWidgets.QLabel('5', self)
        lbl_count.setStyleSheet('QLabel { font-size: 17pt; font-family: Arial; background: palette(highlight); qproperty-alignment: \'AlignTop | AlignHCenter\';  }')
        lbl_count.setFixedSize(*count_size)
        lbl_count.adjustSize()
        # lbl_count.setAlignment(QtCore.Qt.AlignTop)

        stylesheet_btn = 'QPushButton { border: none; background: palette(button); padding: 3px; } QPushButton:hover { border: 1px solid palette(light); background: palette(midlight); }'
        btn_minus = QtWidgets.QPushButton(utils.icon('minus.svg', 180), '', lbl_count)
        btn_plus = QtWidgets.QPushButton(utils.icon('plus.svg', 180), '', lbl_count)
        btn_minus.setStyleSheet(stylesheet_btn)
        btn_plus.setStyleSheet(stylesheet_btn)
        w, h = btn_plus.iconSize().toTuple()
        btn_minus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_minus.setFixedSize(21, 19)
        btn_minus.move(lbl_count.rect().bottomLeft() - btn_minus.rect().bottomLeft())
        btn_plus.setIconSize(QtCore.QSize(round(w * .5), round(h * .5)))
        btn_plus.setFixedSize(21, 19)
        btn_plus.move(lbl_count.rect().bottomRight() - btn_plus.rect().bottomRight())

        lbl_name = QtWidgets.QLabel('Royal Burgonet', self)
        lbl_name.setStyleSheet('QLabel { font-size: 10pt; }')
        lbl_name.setFixedHeight(count_size[1])


        layout_buttons = QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(btn_buy)
        layout_buttons.addWidget(btn_done)

        buy_list = QtWidgets.QListWidget(self)
        buy_list.setSpacing(5)
        buy_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        buy_list.setSizeAdjustPolicy(QtWidgets.QListWidget.AdjustToContents)
        # buy_list.setResizeMode(QtWidgets.QListView.Adjust)
        # buy_list.setMinimumWidth(item1_widget.sizeHint().width())
        # buy_list.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        item1_widget = QtWidgets.QWidget()
        layout_widget = QtWidgets.QHBoxLayout()
        layout_widget.setContentsMargins(0, 0, 0, 0)
        layout_widget.addWidget(lbl_count)
        layout_widget.addWidget(lbl_name)

        # widget_count = QtWidgets.QWidget()
        # widget_count.setObjectName('buttons')
        # layout_widget_count = QtWidgets.QHBoxLayout()
        # layout_widget_count.addWidget(lbl_count)
        # layout_widget_count.setContentsMargins(0, 0, 0, 0)
        # widget_count.setLayout(layout_widget_count)

        layout_widget.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        item1_widget.setLayout(layout_widget)
        item1_widget.adjustSize()

        btn_config = QtWidgets.QPushButton(utils.icon('config.svg', 180), '', item1_widget)
        btn_config.setStyleSheet(stylesheet_btn)
        btn_config.setFixedSize(21, 19)
        btn_config.move(item1_widget.rect().bottomRight() - btn_config.rect().bottomRight())


        print(item1_widget.sizeHint())

        item1 = QtWidgets.QListWidgetItem()
        item1.setSizeHint(item1_widget.sizeHint())
        buy_list.addItem(item1)
        buy_list.setItemWidget(item1, item1_widget)
        # item1.setSizeHint(item1_widget.sizeHint())
        # buy_list.setStyleSheet('QWidget#buttons { background: palette(base); }')
        buy_list.setStyleSheet('QListWidget::item:selected:focus { background: palette(base); }')

        print(item1.sizeHint())
        print(buy_list.width())
        buy_list.adjustSize()

        buy_list.setMinimumWidth(buy_list.sizeHintForColumn(0) + 2 * buy_list.frameWidth() + 2 * buy_list.spacing())
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_buttons)
        layout.addWidget(buy_list)
        print(buy_list.width())
        self.setLayout(layout)
        print(buy_list.width())
        self.buy_list = buy_list

    def _init_ui(self):
        icon_buy = utils.icon('buy.svg', 180, margins=(None, None, _BUTTON_ICON_SPACING, None))
        # btn_buy = QtWidgets.QPushButton(icon_buy, 'Buy', self)
        btn_buy = QtWidgets.QToolButton(self)
        btn_buy.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        action_buy = QtWidgets.QAction(icon_buy, 'Buy', btn_buy)
        btn_buy.addAction(action_buy)
        btn_buy.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn_buy.setDefaultAction(action_buy)
        w, h = btn_buy.iconSize().toTuple()
        btn_buy.setIconSize(QtCore.QSize(round(w * (1 + _BUTTON_ICON_SPACING)), h))
        btn_done = QtWidgets.QPushButton(utils.icon('tick.svg', 180, margins=0.35), 'Remove', self)

        layout_buttons = QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(btn_buy, 1)
        layout_buttons.addWidget(btn_done)

        buy_list = QtWidgets.QListWidget(self)
        buy_list.setMouseTracking(True)
        buy_list.setSpacing(3)
        buy_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        buy_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        buy_list.setSizeAdjustPolicy(QtWidgets.QListWidget.AdjustToContents)
        buy_list.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        corrupts = """+1 to Maximum Power Charges
Socketed Skill Gems get a 90% Cost & Reservation Multiplier
+2 to Level of Socketed Aura Gems
+2 to Level of Socketed AoE Gems
#% increased maximum Life
+2 to Level of Socketed Cold Gems
+2 to Level of Socketed Duration Gems
#% increased Burning Damage
+2 to Level of Socketed Fire Gems
+2 to Level of Socketed Curse Gems
+2 to Level of Socketed Lightning Gems
Regenerate #% of Life per second
+2 to Level of Socketed Warcry Gems
#% increased Effect of Shock
0.5% of Cold Damage Leeched as Life
#% increased maximum Energy Shield
0.5% of Fire Damage Leeched as Life
Cannot be Blinded
0.5% of Lightning Damage Leeched as Life
+2 to Level of Socketed Projectile Gems
+2 to Level of Socketed Trap or Mine Gems










""".splitlines()
        influences = ['hunter', 'elder, shaper', 'redeemer', 'warlord']
        ilvls = list(f'i{i}+' for i in range(56,86))

        bases = """Crown of Eyes
Crown of the Inward Eye
Devoto's Devotion
Abyssus
Alpha's Howl
Asenath's Chant
Viridi's Veil
The Devouring Diadem
Corruption Corona
Royal Burgonet
Lion Pelt""".splitlines()

        import random
        random.seed(42)

        def add_item():
            item_widget = ListItem2(random.randrange(1, 20), random.choice(bases), random.choice(ilvls), random.choice(influences), random.choice(corrupts))
            item = QtWidgets.QListWidgetItem(parent=buy_list)
            item.setSizeHint(item_widget.sizeHint())
            buy_list.addItem(item)
            buy_list.setItemWidget(item, item_widget)

            # item_widget.updateGeometry()
            # item_widget.layout_text.update()
            # item_widget.layout_count.update()
            # item_widget.lbl_name.adjustSize()
            # item.setBackgroundColor(QtGui.QColor('black'))
            # item_widget.update()

        # item1_widget = ListItem(5, 'Royal Burgonet')
        # item1 = QtWidgets.QListWidgetItem(parent=buy_list)
        # item1.setSizeHint(item1_widget.sizeHint())
        # buy_list.addItem(item1)
        # buy_list.setItemWidget(item1, item1_widget)
        # item2_widget = ListItem(3, 'Crown of the Inward Eye')
        # item2 = QtWidgets.QListWidgetItem(parent=buy_list)
        # item2.setSizeHint(item2_widget.sizeHint())
        # buy_list.addItem(item2)
        # buy_list.setItemWidget(item2, item2_widget)
        # print(f'SCROLL {buy_list.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent)}')

        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()
        add_item()

        # buy_list.setStyleSheet('QListWidget::item:selected, QListWidget::item:focus, QListWidget::item:selected:focus { background: palette(base); border: none; }')
        buy_list.setStyleSheet('QListWidget { show-decoration-selected: 0; }')

        # print(
        #     f'BEFORE LAYOUT\n'
        #     f'{buy_list.sizeHint()=}\n'
        #     f'{buy_list.size()=}\n\n'
        #     f'{item1.sizeHint()=}\n'
        #     f'{item1_widget.sizeHint()=}\n'
        #     f'{item1_widget.size()=}\n\n'
        #     f'{item2.sizeHint()=}\n'
        #     f'{item2_widget.sizeHint()=}\n'
        #     f'{item2_widget.size()=}\n'
        # )

        min_width = buy_list.sizeHintForColumn(0) + 2 * buy_list.frameWidth() + 2 * buy_list.spacing()
        buy_list.setMinimumWidth(min_width)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(layout_buttons)
        layout.addSpacing(3)
        layout.addWidget(buy_list)
        self.setLayout(layout)
        self.buy_list = buy_list

        # print(
        #     f'AFTER LAYOUT\n'
        #     f'{min_width=}\n'
        #     f'{buy_list.sizeHint()=}\n'
        #     f'{buy_list.size()=}\n\n'
        #     f'{item1.sizeHint()=}\n'
        #     f'{item1_widget.sizeHint()=}\n'
        #     f'{item1_widget.size()=}\n\n'
        #     f'{item2.sizeHint()=}\n'
        #     f'{item2_widget.sizeHint()=}\n'
        #     f'{item2_widget.size()=}\n'
        # )

        def selection_handler(curr, prev):
            if prev:
                prev_widget = buy_list.itemWidget(prev)
                prev_widget.on_selection(False)
                prev.setSizeHint(prev_widget.sizeHint())
            if curr:
                curr_widget = buy_list.itemWidget(curr)
                curr_widget.on_selection(True)
                curr.setSizeHint(curr_widget.sizeHint())
        buy_list.currentItemChanged.connect(selection_handler)
