import injector
from PyQt5 import QtWidgets

from labbie.ui import base
from labbie.ui import switch


class ResultWidget(base.BaseWidget):

    @injector.inject
    def __init__(self, parent=None):
        super().__init__(parent)

        self.widget_daily = QtWidgets.QWidget(self)
        self.switch_daily = switch.Switch(self.widget_daily, thumb_radius=8, track_radius=5)
        self.lbl_daily = QtWidgets.QLabel('Daily', self.widget_daily)

        self.lbl_search = QtWidgets.QLabel(self)
        self.edit_result = QtWidgets.QTextEdit(self)

        self.edit_result.setReadOnly(True)

        layout_daily = QtWidgets.QHBoxLayout()
        layout_daily.addWidget(self.lbl_daily)
        layout_daily.addWidget(self.switch_daily)
        layout_daily.addSpacing(15)
        layout_daily.setContentsMargins(0, 0, 0, 0)

        self.widget_daily.setLayout(layout_daily)

        layout_top = QtWidgets.QHBoxLayout()
        layout_top.addWidget(self.widget_daily)
        layout_top.addWidget(self.lbl_search, 1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_top)
        layout.addWidget(self.edit_result)
        self.setLayout(layout)

        self.switch_daily.toggled.connect(self.on_daily_toggled)

        self._league_result = None
        self._daily_result = None

    def set_result(self, search, league_result, daily_result=None):
        self._league_result = league_result
        self._daily_result = daily_result

        self.widget_daily.setVisible(league_result is not None and daily_result is not None)

        self.lbl_search.setText(search)
        if league_result is not None:
            self.edit_result.setText(league_result)
        else:
            self.edit_result.setText(daily_result)

    def on_daily_toggled(self, checked):
        self.edit_result.setText(self._daily_result if checked else self._league_result)
