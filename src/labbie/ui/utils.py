import os
import pathlib
from typing import Tuple, Union

from PyQt5 import QtGui, QtWidgets

from labbie import utils

_OBSERVED_ABOUTTOQUIT_SIGNAL = False


def asset_path(subpath: Union[str, pathlib.Path]):
    return utils.assets_dir() / subpath


def fix_taskbar_icon():
    if os.name == "nt":
        import ctypes

        myappid = "labbie.0.1.0"  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def recolored_icon(asset, rgb: Union[int, Tuple[int, int, int]]):
    img = QtGui.QPixmap(str(asset_path(asset)))
    qp = QtGui.QPainter(img)
    qp.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    if isinstance(rgb, int):
        rgb = (rgb, rgb, rgb)
    qp.fillRect(img.rect(), QtGui.QColor.fromRgb(*rgb))
    qp.end()
    return QtGui.QIcon(img)

# NOTE: hack to work around aboutToQuit firing at app initialization
def _exit_handler_wrapper(handler):
    def wrapped():
        global _OBSERVED_ABOUTTOQUIT_SIGNAL
        if not _OBSERVED_ABOUTTOQUIT_SIGNAL:
            _OBSERVED_ABOUTTOQUIT_SIGNAL = True
        else:
            handler()
    return wrapped


def register_exit_handler(handler):
    if not _OBSERVED_ABOUTTOQUIT_SIGNAL:
        handler = _exit_handler_wrapper(handler)
    QtWidgets.QApplication.instance().aboutToQuit.connect(handler)


class CheckboxProperty:
    def __init__(self, widget_fn, tristate=False):
        self.widget_fn = widget_fn
        self.tristate = tristate

    def __get__(self, obj, objtype=None):
        widget = self.widget_fn(obj)
        if not self.tristate:
            return widget.isChecked()
        else:
            return widget.checkState()

    def __set__(self, obj, value):
        widget = self.widget_fn(obj)
        if not self.tristate:
            widget.setChecked(value)
        else:
            widget.setCheckState(value)


def checkbox_property(widget_fn=None, tristate=None):
    if isinstance(tristate, bool):
        def decorator(widget_fn):
            return CheckboxProperty(widget_fn, tristate=tristate)
        return decorator
    else:
        return CheckboxProperty(widget_fn)


class RadioProperty:
    def __init__(self, widget_fn):
        self.widget_fn = widget_fn

    def __get__(self, obj, objtype=None):
        widget = self.widget_fn(obj)
        return widget.checkedId()

    def __set__(self, obj, value):
        if isinstance(value, Enum):
            value = value.value

        widget = self.widget_fn(obj)
        for btn in widget.buttons():
            if widget.id(btn) == value:
                btn.setChecked(True)


def radio_property(widget_fn):
    return RadioProperty(widget_fn)


class TextProperty:
    def __init__(self, widget_fn):
        self.widget_fn = widget_fn

    def __get__(self, obj, objtype=None):
        widget = self.widget_fn(obj)
        return widget.text()

    def __set__(self, obj, value):
        widget = self.widget_fn(obj)
        widget.setText(value)


def text_property(widget_fn):
    return TextProperty(widget_fn)


class ComboBoxProperty:
    def __init__(self, widget_fn):
        self.widget_fn = widget_fn

    def __get__(self, obj, objtype=None):
        widget = self.widget_fn(obj)
        return widget.currentText()

    def __set__(self, obj, value):
        widget = self.widget_fn(obj)
        # TODO (bnorick): use setCurrentText?
        idx = widget.findText(value)
        widget.setCurrentIndex(idx)


def combo_box_property(widget_fn):
    return ComboBoxProperty(widget_fn)


class CheckableComboBoxProperty:
    def __init__(self, widget_fn):
        self.widget_fn = widget_fn

    def __get__(self, obj, objtype=None):
        widget = self.widget_fn(obj)
        return widget.currentData()

    def __set__(self, obj, value):
        widget = self.widget_fn(obj)
        widget.setCheckedTexts(value)


def checkable_combo_box_property(widget_fn):
    return CheckableComboBoxProperty(widget_fn)
