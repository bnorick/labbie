from qtpy import QtCore
from qtpy import QtWidgets

from labbie.ui import base
from labbie.ui import switch
from labbie.ui import utils
from labbie.ui import vertical_tabs

Qt = QtCore.Qt


class SettingsWidget(base.BaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tabs = vertical_tabs.VTabWidget()

        # General tab
        widget_general = QtWidgets.QWidget()

        lbl_league = QtWidgets.QLabel('League', self)
        self.switch_league = switch.Switch(self, thumb_radius=8, track_radius=5)

        lbl_daily = QtWidgets.QLabel('Daily', self)
        self.switch_daily = switch.Switch(self, thumb_radius=8, track_radius=5)

        # UI tab
        widget_ui = QtWidgets.QWidget()
        lbl_show_on_taskbar = QtWidgets.QLabel('Show on taskbar', self)
        self.switch_show_on_taskbar = switch.Switch(self, thumb_radius=8, track_radius=5)

        self.btn_reset_window_positions = QtWidgets.QPushButton('Reset Window Positions', self)
        # size = self.btn_reset_window_positions.sizeHint()
        # self.btn_reset_window_positions.setMinimumWidth(size.width() + 12)

        # Screen capture tab
        widget_screen_capture = QtWidgets.QWidget()
        lbl_hotkey = QtWidgets.QLabel('Hotkey', self)
        self.edit_hotkey = QtWidgets.QLineEdit(self)

        lbl_clear = QtWidgets.QLabel('Clear previous results', self)
        self.switch_clear = switch.Switch(self, thumb_radius=8, track_radius=5)

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

        # Updates tab
        widget_updates = QtWidgets.QWidget()
        lbl_auto_update = QtWidgets.QLabel('Auto update', self)
        self.switch_auto_update = switch.Switch(self, thumb_radius=8, track_radius=5)
        lbl_install_prereleases = QtWidgets.QLabel('Install pre-releases', self)
        self.switch_install_prereleases = switch.Switch(self, thumb_radius=8, track_radius=5)
        self.btn_check_for_update = QtWidgets.QPushButton('Check for Update', self)

        self.btn_save = QtWidgets.QPushButton('Save', self)
        self.btn_cancel = QtWidgets.QPushButton('Cancel', self)

        layout_general = QtWidgets.QGridLayout()
        layout_general.addWidget(lbl_league, 0, 0)
        layout_general.addWidget(self.switch_league, 0, 1)
        layout_general.addWidget(lbl_daily, 1, 0)
        layout_general.addWidget(self.switch_daily, 1, 1)
        layout_general.setColumnStretch(0, 0)
        layout_general.setColumnStretch(1, 0)
        layout_general.setColumnStretch(2, 1)
        layout_general.setRowStretch(2, 1)

        # layout_general = QtWidgets.QHBoxLayout()
        # layout_general.addLayout(layout_general_content)
        # layout_general.addStretch(1)
        widget_general.setLayout(layout_general)

        layout_ui = QtWidgets.QGridLayout()
        layout_ui.addWidget(lbl_show_on_taskbar, 0, 0)
        layout_ui.addWidget(self.switch_show_on_taskbar, 0, 1)
        layout_ui.addWidget(self.btn_reset_window_positions, 2, 0, 1, 3)
        layout_ui.setColumnStretch(0, 0)
        layout_ui.setColumnStretch(1, 0)
        layout_ui.setColumnStretch(2, 1)
        layout_ui.setRowStretch(1, 1)

        # layout_ui = QtWidgets.QHBoxLayout()
        # layout_ui.addLayout(layout_ui_content)
        # layout_ui.addStretch(1)
        widget_ui.setLayout(layout_ui)

        layout_capture_ungrouped_content = QtWidgets.QGridLayout()
        layout_capture_ungrouped_content.addWidget(lbl_hotkey, 0, 0)
        layout_capture_ungrouped_content.addWidget(self.edit_hotkey, 0, 1)
        layout_capture_ungrouped_content.addWidget(lbl_clear, 1, 0)
        layout_capture_ungrouped_content.addWidget(self.switch_clear, 1, 1)

        layout_capture_ungrouped = QtWidgets.QHBoxLayout()
        layout_capture_ungrouped.addLayout(layout_capture_ungrouped_content)
        layout_capture_ungrouped.addStretch(1)

        layout_bounds_content = QtWidgets.QGridLayout()
        layout_bounds_content.addWidget(lbl_bounds_left, 0, 0, Qt.AlignmentFlag.AlignRight)
        layout_bounds_content.addWidget(self.edit_left, 0, 1)
        layout_bounds_content.addWidget(lbl_bounds_top, 0, 2, Qt.AlignmentFlag.AlignRight)
        layout_bounds_content.addWidget(self.edit_top, 0, 3)
        layout_bounds_content.addWidget(lbl_bounds_right, 1, 0, Qt.AlignmentFlag.AlignRight)
        layout_bounds_content.addWidget(self.edit_right, 1, 1)
        layout_bounds_content.addWidget(lbl_bounds_bottom, 1, 2, Qt.AlignmentFlag.AlignRight)
        layout_bounds_content.addWidget(self.edit_bottom, 1, 3)
        layout_bounds_content.addWidget(self.btn_select_bounds, 2, 0, 1, 2)

        layout_bounds = QtWidgets.QHBoxLayout()
        layout_bounds.addLayout(layout_bounds_content)
        layout_bounds.addStretch(1)

        group_bounds.setLayout(layout_bounds)

        layout_screen_capture = QtWidgets.QVBoxLayout()
        layout_screen_capture.addLayout(layout_capture_ungrouped)
        layout_screen_capture.addWidget(group_bounds)

        widget_screen_capture.setLayout(layout_screen_capture)

        layout_updates = QtWidgets.QGridLayout()
        layout_updates.addWidget(lbl_auto_update, 0, 0)
        layout_updates.addWidget(self.switch_auto_update, 0, 1)
        layout_updates.addWidget(lbl_install_prereleases, 1, 0)
        layout_updates.addWidget(self.switch_install_prereleases, 1, 1)
        layout_updates.addWidget(self.btn_check_for_update, 3, 0, 1, 3)
        layout_updates.setColumnStretch(0, 0)
        layout_updates.setColumnStretch(1, 0)
        layout_updates.setColumnStretch(2, 1)
        layout_updates.setRowStretch(2, 1)

        widget_updates.setLayout(layout_updates)

        layout_actions = QtWidgets.QHBoxLayout()
        layout_actions.addStretch(1)
        layout_actions.addWidget(self.btn_save)
        layout_actions.addWidget(self.btn_cancel)

        self.tabs.addTab(widget_general, 'General')
        self.tabs.addTab(widget_ui, 'User Interface')
        self.tabs.addTab(widget_screen_capture, 'Screen Capture')
        self.tabs.addTab(widget_updates, 'Updates')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addLayout(layout_actions)
        self.setLayout(layout)

        self.btn_cancel.clicked.connect(self.close)

        self.setWindowTitle('Settings')
        self.center_on_screen()

    def set_select_button_text(self, text):
        self.btn_select_bounds.setText(text)

    def set_select_bounds_handler(self, handler):
        self._connect_signal_to_slot(self.btn_select_bounds.clicked, handler)

    def set_reset_window_positions_handler(self, handler):
        self._connect_signal_to_slot(self.btn_reset_window_positions.clicked, handler)

    def set_check_for_update_handler(self, handler):
        self._connect_signal_to_slot(self.btn_check_for_update.clicked, handler)

    def set_save_handler(self, handler):
        self._connect_signal_to_slot(self.btn_save.clicked, handler)

    @utils.checkbox_property
    def league(self):
        return self.switch_league

    @utils.checkbox_property
    def daily(self):
        return self.switch_daily

    @utils.checkbox_property
    def show_on_taskbar(self):
        return self.switch_show_on_taskbar

    @utils.text_property
    def hotkey(self):
        return self.edit_hotkey

    @utils.checkbox_property
    def clear_previous(self):
        return self.switch_clear

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

    @utils.checkbox_property
    def auto_update(self):
        return self.switch_auto_update

    @utils.checkbox_property
    def install_prereleases(self):
        return self.switch_install_prereleases
