from PyQt5 import QtCore
from PyQt5 import QtWidgets

from labbie.ui import base
from labbie.ui import switch
from labbie.ui import utils

Qt = QtCore.Qt


class SettingsWidget(base.BaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        group_builds = QtWidgets.QGroupBox('Build Scrapes', self)

        lbl_league = QtWidgets.QLabel('League', self)
        self.switch_league = switch.Switch(self, thumb_radius=8, track_radius=5)

        lbl_daily = QtWidgets.QLabel('Daily', self)
        self.switch_daily = switch.Switch(self, thumb_radius=8, track_radius=5)

        group_screen_capture = QtWidgets.QGroupBox('Screen Capture', self)

        lbl_hotkey = QtWidgets.QLabel('Hotkey', self)
        self.edit_hotkey = QtWidgets.QLineEdit(self)

        group_bounds = QtWidgets.QGroupBox('Capture Bounds', self)
        lbl_bounds_left = QtWidgets.QLabel('Left', self)
        self.edit_left = QtWidgets.QLineEdit(self)
        lbl_bounds_top = QtWidgets.QLabel('Top', self)
        self.edit_top = QtWidgets.QLineEdit(self)
        lbl_bounds_right = QtWidgets.QLabel('Right', self)
        self.edit_right = QtWidgets.QLineEdit(self)
        lbl_bounds_bottom = QtWidgets.QLabel('Bottom', self)
        self.edit_bottom = QtWidgets.QLineEdit(self)
        self.btn_select_bounds = QtWidgets.QPushButton('Select', self)

        self.btn_save = QtWidgets.QPushButton('Save', self)
        self.btn_cancel = QtWidgets.QPushButton('Cancel', self)

        layout_active = QtWidgets.QGridLayout()
        layout_active.addWidget(lbl_league, 0, 0)
        layout_active.addWidget(self.switch_league, 0, 1)
        layout_active.addWidget(lbl_daily, 1, 0)
        layout_active.addWidget(self.switch_daily, 1, 1)

        layout_builds = QtWidgets.QHBoxLayout()
        layout_builds.addLayout(layout_active)
        layout_builds.addStretch(1)
        group_builds.setLayout(layout_builds)

        lbl_clear = QtWidgets.QLabel('Clear previous results', self)
        self.switch_clear = switch.Switch(self, thumb_radius=8, track_radius=5)

        layout_capture_general = QtWidgets.QGridLayout()
        layout_capture_general.addWidget(lbl_hotkey, 0, 0)
        layout_capture_general.addWidget(self.edit_hotkey, 0, 1)
        layout_capture_general.addWidget(lbl_clear, 1, 0)
        layout_capture_general.addWidget(self.switch_clear, 1, 1)

        layout_capture_top = QtWidgets.QHBoxLayout()
        layout_capture_top.addLayout(layout_capture_general)
        layout_capture_top.addStretch(1)

        layout_bounds_vals_grid = QtWidgets.QGridLayout()
        layout_bounds_vals_grid.addWidget(lbl_bounds_left, 0, 0, Qt.AlignmentFlag.AlignRight)
        layout_bounds_vals_grid.addWidget(self.edit_left, 0, 1)
        layout_bounds_vals_grid.addWidget(lbl_bounds_top, 0, 2, Qt.AlignmentFlag.AlignRight)
        layout_bounds_vals_grid.addWidget(self.edit_top, 0, 3)
        layout_bounds_vals_grid.addWidget(lbl_bounds_right, 1, 0, Qt.AlignmentFlag.AlignRight)
        layout_bounds_vals_grid.addWidget(self.edit_right, 1, 1)
        layout_bounds_vals_grid.addWidget(lbl_bounds_bottom, 1, 2, Qt.AlignmentFlag.AlignRight)
        layout_bounds_vals_grid.addWidget(self.edit_bottom, 1, 3)

        layout_bounds_vals = QtWidgets.QHBoxLayout()
        layout_bounds_vals.addLayout(layout_bounds_vals_grid)
        layout_bounds_vals.addStretch(1)

        layout_select = QtWidgets.QHBoxLayout()
        layout_select.addWidget(self.btn_select_bounds)
        layout_select.addStretch(1)

        layout_bounds = QtWidgets.QVBoxLayout()
        layout_bounds.addLayout(layout_bounds_vals)
        layout_bounds.addLayout(layout_select)

        group_bounds.setLayout(layout_bounds)

        layout_screen_capture = QtWidgets.QVBoxLayout()
        layout_screen_capture.addLayout(layout_capture_top)
        layout_screen_capture.addWidget(group_bounds)

        group_screen_capture.setLayout(layout_screen_capture)

        layout_actions = QtWidgets.QHBoxLayout()
        layout_actions.addStretch(1)
        layout_actions.addWidget(self.btn_save)
        layout_actions.addWidget(self.btn_cancel)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(group_builds)
        layout.addWidget(group_screen_capture)
        layout.addLayout(layout_actions)
        self.setLayout(layout)

        self.btn_cancel.clicked.connect(self.close)

        self.setWindowTitle('Settings')
        self.center_on_screen()

    def set_select_bounds_handler(self, handler):
        self._connect_signal_to_slot(self.btn_select_bounds.clicked, handler)

    def set_save_handler(self, handler):
        self._connect_signal_to_slot(self.btn_save.clicked, handler)

    @utils.checkbox_property
    def league(self):
        return self.switch_league

    @utils.checkbox_property
    def daily(self):
        return self.switch_daily

    @utils.checkbox_property
    def clear_previous(self):
        return self.switch_clear

    @utils.text_property
    def hotkey(self):
        return self.edit_hotkey

    @utils.text_property
    def left(self):
        return self.edit_left

    @utils.text_property
    def top(self):
        return self.edit_top

    @utils.text_property
    def right(self):
        return self.edit_right

    @utils.text_property
    def bottom(self):
        return self.edit_bottom
