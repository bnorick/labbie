import keyboard
from PyQt5 import QtCore


class Hotkey(QtCore.QObject):
    pressed = QtCore.pyqtSignal()

    def __init__(self, hotkey):
        super().__init__()
        self.hotkey = hotkey

    def start(self, handler=None):
        keyboard.add_hotkey(self.hotkey, self.pressed.emit, suppress=True)
        if handler:
            self.pressed.connect(handler)

    def stop(self, disconnect=True):
        if disconnect:
            self.pressed.disconnect()
        keyboard.remove_hotkey(self.hotkey)

    def set_hotkey(self, hotkey):
        if self.hotkey == hotkey:
            return

        self.stop(disconnect=False)
        self.start()
