from typing import Tuple, Union
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from labbie.ui import base
from labbie.ui import switch
from labbie.ui import utils
from labbie import version

Qt = QtCore.Qt


class AboutWidget(base.BaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        lbl_title = QtWidgets.QLabel('Labbie', self)
        lbl_title.setStyleSheet("QLabel{font-size: 12pt; font-weight: bold;}")
        lbl_version = QtWidgets.QLabel(f'v{version.__version__}', self)
        lbl_version.setStyleSheet("QLabel{font-size: 9pt; font-weight: bold;}")

        details = ('This tool was born out of a desire to better understand the Lab economy.<br />'
                   'It is a labor of love by Brandon Norick, who pays to host the data used by Labbie.<br />'
                   'If you find the tool useful, please consider donating through '
                   '<a href="https://www.paypal.com/donate?hosted_button_id=4QXG9CPFYF5UJ">Paypal</a> '
                   'or <a href="https://www.patreon.com/bnorick">Patreon</a>.<br />Even the smallest amounts help!')
        lbl_details = QtWidgets.QLabel(details)
        lbl_details.setStyleSheet("QLabel{font-size: 9pt;}")
        lbl_details.setOpenExternalLinks(True)

        self.btn_relaunch = QtWidgets.QPushButton(self)
        self.btn_open_data = QtWidgets.QPushButton(utils.recolored_icon('folder_space.svg', 180), 'Open Data', self)
        self.btn_open_data.setIconSize(QtCore.QSize(24, 16))
        self.btn_open_logs = QtWidgets.QPushButton(utils.recolored_icon('folder_space.svg', 180), 'Open Logs', self)
        self.btn_open_logs.setIconSize(QtCore.QSize(24, 16))

        layout_buttons = QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(self.btn_relaunch)
        layout_buttons.addWidget(self.btn_open_data)
        layout_buttons.addWidget(self.btn_open_logs)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 0, 10, 10)
        layout.addWidget(lbl_title, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_version, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(lbl_details)
        layout.addLayout(layout_buttons)
        self.setLayout(layout)

        self.center_on_screen()

    def set_relauch_text(self, text):
        self.btn_relaunch.setText(text)

    def set_relaunch_handler(self, handler):
        self._connect_signal_to_slot(self.btn_relaunch.clicked, handler)

    def set_open_data_handler(self, handler):
        self._connect_signal_to_slot(self.btn_open_data.clicked, handler)

    def set_open_logs_handler(self, handler):
        self._connect_signal_to_slot(self.btn_open_logs.clicked, handler)

    def exit(self):
        QtWidgets.QApplication.exit()
