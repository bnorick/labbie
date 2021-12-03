import asyncio

from qtpy import QtCore
from qtpy import QtWidgets

from labbie.ui import utils as ui_utils
from labbie.vendor.qtmodern import windows

Qt = QtCore.Qt


class UpdateMessageBox(windows.ModernMessageBox):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dialog.setWindowFlags(self._dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Update Available')
        # TODO(bnorick): add icon back
        # self.setIconPixmap(
        #     ui_utils.recolored_icon('update.svg', rgb=180).pixmap(QtCore.QSize(35, 35)))

        self.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.btn_update = self.addButton('Update', QtWidgets.QMessageBox.AcceptRole)
        self.btn_remind = self.addButton('Remind Me Later', QtWidgets.QMessageBox.ActionRole)
        self.btn_skip = self.addButton('Skip Version', QtWidgets.QMessageBox.RejectRole)
        # self.setEscapeButton(self.btn_remind)

        self.btn_update.clicked.connect(self.on_update)
        self.btn_remind.clicked.connect(self.on_remind)
        self.btn_skip.clicked.connect(self.on_skip)

        self._future = None

    def ask(self, text: str, show_skip: bool, future: asyncio.Future):
        self._future = future
        self.setText(text)
        self.btn_skip.setVisible(show_skip)
        self.show()

    def on_update(self):
        if self._future:
            self._future.set_result('update')
        self._dialog.close()

    def on_remind(self):
        if self._future:
            self._future.set_result('remind')
        self._dialog.close()

    def on_skip(self):
        if self._future:
            self._future.set_result('skip')
        self._dialog.close()

    def tell(self, text: str):
        self.setWindowTitle('No Update Available')
        # self.removeButton(self.btn_update)
        # self.removeButton(self.btn_remind)
        self.btn_update.hide()
        self.btn_remind.hide()
        self.setText(text)
        self.btn_skip.setText('OK')

        self.show()
        # self.exec_()
        # self.hide()
