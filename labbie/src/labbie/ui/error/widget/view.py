from qtpy import QtCore
from qtpy import QtWidgets

from labbie.ui import base

Qt = QtCore.Qt


class ErrorWidget(base.BaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lbl_error = QtWidgets.QLabel(self)
        self.lbl_error.setStyleSheet("QLabel{font-size: 12pt;}")
        self.lbl_error.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.btn_ok = QtWidgets.QPushButton('OK', self)

        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_error)
        layout.addSpacing(10)
        layout.addWidget(self.btn_ok, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

        self.btn_ok.clicked.connect(self.close)

        self.setWindowTitle('Error')
        self.center_on_screen()

    def set_error(self, error: str):
        self.lbl_error.setText(error)
