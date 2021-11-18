from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from updater.vendor.qtmodern import windows

Qt = QtCore.Qt


class UpdateWindow(windows.ModernWindow):
    def __init__(self, parent=None):
        widget = QtWidgets.QWidget()
        widget.setWindowTitle('Updater')

        progress_bar = QtWidgets.QProgressBar()
        lbl_status = QtWidgets.QLabel('Status')
        edit_status = QtWidgets.QTextEdit()

        btn_show = QtWidgets.QPushButton('Show More')
        btn_act = QtWidgets.QPushButton('Cancel')

        progress_bar.setMinimumWidth(450)
        lbl_status.hide()
        edit_status.hide()
        edit_status.setReadOnly(True)
        btn_show.clicked.connect(self.on_show)
        btn_act.clicked.connect(self.on_act)

        layout_buttons = QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(btn_show)
        layout_buttons.addStretch(1)
        layout_buttons.addWidget(btn_act)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(progress_bar)
        layout.addWidget(lbl_status)
        layout.addWidget(edit_status)
        layout.addLayout(layout_buttons)
        widget.setLayout(layout)
        layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        widget.adjustSize()

        self.status_shown = False
        self.progress_bar = progress_bar
        self.lbl_status = lbl_status
        self.edit_status = edit_status
        self.btn_show = btn_show
        self.btn_act = btn_act
        self.widget = widget

        super().__init__(widget, parent=parent)
        self.set_buttons(minimize=True, maximize=False, close=True)

        # NOTE: SetFixedSize here allows the window to resize correctly after show/hide
        self.layout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.done = False
        self.task = None
        self.messages = 0

    def set_status_visibility(self, visible):
        self.lbl_status.setVisible(visible)
        self.edit_status.setVisible(visible)
        self.btn_show.setText('Show ' + ('Less' if visible else 'More'))

    def on_done(self, error=False):
        if error:
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor('red'))
            self.progress_bar.setPalette(palette)
        self.btn_act.setText('Exit')
        self.done = True

    def set_task(self, task):
        self.task = task

    def on_show(self):
        show = not self.status_shown
        self.status_shown = show
        self.set_status_visibility(show)

    def on_act(self):
        if self.done:
            self.close()
        if self.task:
            print(self.task)
            self.task.cancel()
        self.on_done(error=True)

    def set_progress(self, progress):
        self.progress_bar.setValue(progress)
        if progress == 100:
            self.on_done()

    def add_message(self, message: str, last=False, error=False):
        self.edit_status.moveCursor(QtGui.QTextCursor.Start, QtGui.QTextCursor.MoveAnchor)
        if not self.messages:
            suffix = ''
        elif error or last or self.messages == 1:
            suffix = '\n\n'
        else:
            suffix = '\n'
        self.messages += 1
        self.edit_status.insertPlainText(message + suffix)
        if error:
            self.set_status_visibility(visible=True)
            self.on_done(error=error)
        if last:
            self.set_status_visibility(visible=True)

    def set_buttons(self, minimize=None, maximize=None, close=None):
        kwargs = {}
        if minimize is not None:
            kwargs['minimize'] = minimize
        if maximize is not None:
            kwargs['maximize'] = maximize
        if close is not None:
            kwargs['close'] = close
        self._set_buttons(**kwargs)

    def _set_buttons(self, **kwargs):
        flags = self.windowFlags()

        hints = {
            'minimize': Qt.WindowMinimizeButtonHint,
            'maximize': Qt.WindowMaximizeButtonHint,
            'close': Qt.WindowCloseButtonHint
        }

        for name, value in kwargs.items():
            if hint := hints.get(name):
                if value:
                    flags |= hint
                else:
                    flags &= ~hint
            else:
                raise ValueError(f'Invalid keyword argument "{name}"')

        self.setWindowFlags(flags)