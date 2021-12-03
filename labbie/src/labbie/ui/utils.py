import pathlib
import time
from typing import Optional, Tuple, Union

import loguru
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from labbie import utils

logger = loguru.logger
# _OBSERVED_ABOUTTOQUIT_SIGNAL = False
_IGNORE_ABOUTTOQUIT_UNTIL = time.monotonic() + 3
_MarginType = Union[None, int, float]


def asset_path(subpath: Union[str, pathlib.Path]):
    return utils.assets_dir() / subpath


def fix_taskbar_icon():
    import ctypes
    myappid = 'labbie.0.1.0'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def asset_pixmap(asset, color: Union[None, str, int, Tuple[int, int, int]],
                 size: Optional[Tuple[int, int]] = None,
                 margins: Optional[Tuple[_MarginType, _MarginType, _MarginType, _MarginType]] = None):
    if not isinstance(color, (str, int, tuple, type(None))):
        raise ValueError(f'Invalid color argument, expected None or a value of type int or tuple but got '
                         f'type "{type(color).__name__}".')

    pixmap = QtGui.QPixmap(str(asset_path(asset)))
    if all(arg is None for arg in (color, size, margins)):
        return pixmap

    if size is None:
        size = pixmap.size().toTuple()
    else:
        if pixmap.size().toTuple() != size:
            pixmap = pixmap.scaled(*size)

    pixmap_width, pixmap_height = size
    x, y = 0, 0

    if margins is not None:
        if isinstance(margins, (int, float)):
            margins = (margins, margins, margins, margins)

        for margin, direction in zip(margins, ('left', 'top', 'right', 'bottom')):
            if margin and margin < 0:
                raise ValueError(f'Invalid {direction} margin, expected a non-negative value but got {margin}.')

        width, height = size
        left, top, right, bottom = margins
        if left:
            if isinstance(left, float):
                left = round(left * pixmap_width)
            width += left
            x += left

        if right:
            if isinstance(right, float):
                right = round(right * pixmap_width)
            width += right

        if top:
            if isinstance(top, float):
                top = round(top * pixmap_height)
            height += top
            y += top

        if bottom:
            if isinstance(bottom, float):
                bottom = round(bottom * pixmap_height)
            height += bottom

        size = (width, height)

    result_pixmap = QtGui.QPixmap(*size)
    result_pixmap.fill(QtCore.Qt.transparent)
    qp = QtGui.QPainter(result_pixmap)
    qp.drawPixmap(x, y, pixmap)
    if color:
        qp.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        if isinstance(color, int):
            color = QtGui.QColor(color, color, color)
        elif isinstance(color, str):
            color = QtGui.QColor(color)
        else:
            color = QtGui.QColor(*color)

        qp.fillRect(x, y, pixmap_width, pixmap_height, color)
    qp.end()
    return result_pixmap


def icon(asset, *args, **kwargs):
    pixmap = asset_pixmap(asset, *args, **kwargs)
    return QtGui.QIcon(pixmap)


# NOTE: hack to work around aboutToQuit firing at app initialization
def _exit_handler_wrapper(handler):
    def wrapped():
        # global _OBSERVED_ABOUTTOQUIT_SIGNAL
        # if not _OBSERVED_ABOUTTOQUIT_SIGNAL:
        #     _OBSERVED_ABOUTTOQUIT_SIGNAL = True
        #     logger.debug('FIRST OBSERVED ABOUT TO QUIT')
        # else:
        #     logger.debug('SUBSEQUENT OBSERVED ABOUT TO QUIT')
        #     handler()
        if time.monotonic() > _IGNORE_ABOUTTOQUIT_UNTIL:
            handler()
        else:
            logger.debug(f'Ignoring early aboutToQuit')

    return wrapped


def register_exit_handler(handler):
    # if not _OBSERVED_ABOUTTOQUIT_SIGNAL:
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
