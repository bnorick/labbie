import injector
from PyQt5 import QtWidgets

from labbie.ui import base


class ResultWidget(base.BaseWidget):

    @injector.inject
    def __init__(self, parent=None):
        super().__init__(parent)

        self.lbl_search = QtWidgets.QLabel(self)
        self.edit_result = QtWidgets.QTextEdit(self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.lbl_search)
        layout.addWidget(self.edit_result)
        self.setLayout(layout)

    def set_result(self, search, result):
        self.lbl_search.setText(search)
        self.edit_result.setText(result)
