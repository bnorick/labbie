import pathlib
from typing import Union

from labbie import utils


def asset_path(subpath: Union[str, pathlib.Path]):
    return utils.assets_dir() / subpath


def fix_taskbar_icon():
    import ctypes
    myappid = 'labbie.0.1.0'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


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
