from typing import Dict, List, Optional
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from labbie.ui import base
from labbie.ui import checkable_combo
from labbie.ui import fuzzy_combo
from labbie.ui import utils

Qt = QtCore.Qt


class TabBar(QtWidgets.QTabBar):

    middleClicked = QtCore.pyqtSignal(int)

    def __init__(self):
        super(QtWidgets.QTabBar, self).__init__()
        self.previousMiddleIndex = -1

    def mousePressEvent(self, mouseEvent):
        if mouseEvent.button() == Qt.MidButton:
            self.previousIndex = self.tabAt(mouseEvent.pos())
        QtWidgets.QTabBar.mousePressEvent(self, mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        if mouseEvent.button() == Qt.MidButton and \
            self.previousIndex == self.tabAt(mouseEvent.pos()):
            self.middleClicked.emit(self.previousIndex)
        self.previousIndex = -1
        QtWidgets.QTabBar.mouseReleaseEvent(self, mouseEvent)


class SearchWidget(base.BaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        lbl_mod = QtWidgets.QLabel('Enchant', self)
        self.combo_mod = fuzzy_combo.FuzzyComboBox(self)
        lbl_exact_mod = QtWidgets.QLabel('Exact', self)
        self.chk_exact_mod = QtWidgets.QCheckBox(self)
        self.btn_search_mod = QtWidgets.QPushButton('Search', self)

        lbl_base = QtWidgets.QLabel('Base', self)
        self.combo_base = fuzzy_combo.FuzzyComboBox(self)
        lbl_ilvl = QtWidgets.QLabel('ilvl', self)
        self.edit_ilvl = QtWidgets.QLineEdit(self)
        lbl_influence = QtWidgets.QLabel('Influence', self)
        self.chkcombo_influences = checkable_combo.CheckableComboBox(self, max_checked=2)
        self.btn_search_base = QtWidgets.QPushButton('Search', self)

        self.btn_all = QtWidgets.QPushButton('All', self)
        self.btn_screen_capture = QtWidgets.QPushButton('Screen Capture', self)
        lbl_exact_screen_capture = QtWidgets.QLabel('Exact', self)
        self.chk_exact_screen_capture = QtWidgets.QCheckBox(self)

        self.tabs = QtWidgets.QTabWidget(self)
        self.tab_bar = TabBar()
        self.tabs.setTabBar(self.tab_bar)
        self.tab_bar.middleClicked.connect(self.on_tab_middle_click)

        self.combo_mod.setEditable(True)
        self.combo_base.setEditable(True)

        layout_mod_section = QtWidgets.QVBoxLayout()

        layout_mod = QtWidgets.QHBoxLayout()
        layout_mod.addWidget(lbl_mod)
        layout_mod.addWidget(self.combo_mod, 1)
        layout_mod.addWidget(lbl_exact_mod)
        layout_mod.addWidget(self.chk_exact_mod)

        layout_mod_search = QtWidgets.QHBoxLayout()
        layout_mod_search.addWidget(self.btn_search_mod, 1)

        layout_mod_section.addLayout(layout_mod)
        layout_mod_section.addLayout(layout_mod_search)

        layout_base_section = QtWidgets.QVBoxLayout()

        layout_base = QtWidgets.QHBoxLayout()
        layout_base.addWidget(lbl_base)
        layout_base.addWidget(self.combo_base, 1)
        layout_base.addWidget(lbl_ilvl)
        layout_base.addWidget(self.edit_ilvl)
        layout_base.addWidget(lbl_influence)
        layout_base.addWidget(self.chkcombo_influences)

        layout_base_search = QtWidgets.QHBoxLayout()
        layout_base_search.addWidget(self.btn_search_base, 1)

        layout_base_section.addLayout(layout_base)
        layout_base_section.addLayout(layout_base_search)

        layout_screen_capture = QtWidgets.QHBoxLayout()
        layout_screen_capture.addWidget(self.btn_all)
        layout_screen_capture.addWidget(self.btn_screen_capture, 1)
        layout_screen_capture.addWidget(lbl_exact_screen_capture)
        layout_screen_capture.addWidget(self.chk_exact_screen_capture)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_mod_section)
        layout.addSpacing(10)
        layout.addLayout(layout_base_section)
        layout.addSpacing(10)
        layout.addLayout(layout_screen_capture)
        layout.addSpacing(10)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.setWindowTitle('Search Enchants')
        self.center_on_screen(adjust_size=False)

    def on_tab_middle_click(self, index):
        self.tabs.removeTab(index)

    def set_exact_mod_handler(self, handler):
        self._connect_signal_to_slot(self.chk_exact_mod.toggled, handler)

    def set_search_mod_handler(self, handler):
        self._connect_signal_to_slot(self.btn_search_mod.clicked, handler)

    def set_search_base_handler(self, handler):
        self._connect_signal_to_slot(self.btn_search_base.clicked, handler)

    def set_all_handler(self, handler):
        self._connect_signal_to_slot(self.btn_all.clicked, handler)

    def set_screen_capture_handler(self, handler):
        self._connect_signal_to_slot(self.btn_screen_capture.clicked, handler)

    def set_influence_options(self, influences, data):
        self.chkcombo_influences.addItems(influences, data)

    def set_mods(self, mods: List[str], equivalent_mods: Optional[Dict[str, str]]):
        if equivalent_mods:
            prev_selected = equivalent_mods.get(self.combo_mod.currentText())
        else:
            prev_selected = self.combo_mod.currentText()

        self.combo_mod.clear()
        selected = False
        for index, mod in enumerate(mods):
            select = (prev_selected == mod)
            selected |= select
            self.combo_mod.addItem(mod)
            if select:
                self.combo_mod.setCurrentIndex(index)

        if not selected:
            self.combo_mod.setCurrentIndex(0)

        # TODO: remove
        self.combo_mod.setCurrentText('Tornado Shot fires an additional secondary Projectile')

    def set_mod_text(self, index, text):
        self.combo_mod.setItemText(index, text)

    def set_bases(self, bases: List[str]):
        prev_selected = self.combo_base.currentText()
        self.combo_base.clear()
        selected = False
        for index, base in enumerate(bases):
            select = (prev_selected == base)
            selected |= select
            self.combo_base.addItem(base)
            if select:
                self.combo_base.setCurrentIndex(index)

        if not selected:
            self.combo_base.setCurrentIndex(0)

    def add_result_tab(self, title, widget: QtWidgets.QWidget):
        self.tabs.addTab(widget, title)

    def clear_results(self):
        for _ in range(self.tabs.count()):
            self.tabs.removeTab(0)

    # Properties
    @utils.combo_box_property
    def mod(self):
        return self.combo_mod

    @utils.checkbox_property
    def exact_mod(self):
        return self.chk_exact_mod

    @utils.combo_box_property
    def base(self):
        return self.combo_base

    @utils.text_property
    def ilvl(self):
        return self.edit_ilvl

    @utils.checkable_combo_box_property
    def influences(self):
        return self.chkcombo_influences

    @utils.checkbox_property
    def exact_screen_capture(self):
        return self.chk_exact_screen_capture
