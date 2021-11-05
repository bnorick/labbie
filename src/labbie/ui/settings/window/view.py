from labbie.ui import base
from labbie.ui.settings.widget import view as settings_widget


class SettingsWindow(base.BaseWindow):

    def __init__(self, widget: settings_widget.SettingsWidget):
        super().__init__(widget=widget)
        self.set_buttons(minimize=True, close=True)
