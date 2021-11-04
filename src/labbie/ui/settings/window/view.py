from sniper.client.ui.base import BaseWindow
from sniper.client.ui.flip_assistant.widget.view import FlipAssistantWidget


class FlipAssistantWindow(BaseWindow):
    def __init__(self, widget: FlipAssistantWidget):
        super().__init__(widget=widget)
        self.set_buttons(close=True)
