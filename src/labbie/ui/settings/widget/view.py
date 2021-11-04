from functools import partial
from operator import itemgetter
from typing import Any, Dict, List

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QCursor, QIcon, QPixmap
from PyQt5.QtWidgets import QAbstractItemView, QAction, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu, QMessageBox, QProgressBar, QPushButton, QVBoxLayout
from loguru import logger
from sniper.client.ui.util import HLine, asset_path

import sniper.vendor.qtmodern.windows as qtmodern_windows
from sniper.client.ui.base import BaseWidget
from sniper.client.ui.searches.widget.view import SearchesWidget


class FlipAssistantWidget(SearchesWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__init_ui()

    def __init_ui(self):
        self.list_searches.setSelectionMode(QAbstractItemView.SingleSelection)

        self.btn_new.hide()
        self.btn_clone.hide()
        self.btn_delete.hide()
        self.btn_offer_actual.hide()
        self.btn_flip_assistant.hide()

        self.setWindowTitle('Flip Assistant')

        self.btn_go = QPushButton('Go', self)
        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_copy = QPushButton('Copy to Clipboard', self)

        self.btn_cancel.hide()
        self.btn_copy.setEnabled(False)

        self.layout_quick_actions.insertWidget(0, self.btn_go)
        self.layout_quick_actions.insertWidget(1, self.btn_cancel)
        self.layout_quick_actions.insertWidget(2, self.btn_copy)
        self.layout_quick_actions.insertWidget(3, HLine(self))

    def closeEvent(self, event: QCloseEvent):
        logger.debug('closeEvent')
        if self._searches is not None:
            logger.debug('signalling')
            self.signal_close.emit()
        event.accept()

    def set_enabled_buttons(self, copy=None, **kwargs):
        if copy is not None:
            self.btn_copy.setEnabled(copy)
        super().set_enabled_buttons(**kwargs)

    def set_visible_buttons(self, go=None, cancel=None):
        if go is not None:
            self.btn_go.setVisible(go)
        if cancel is not None:
            self.btn_cancel.setVisible(cancel)

    def set_results(self, searches: Dict[str, str], extras: Dict[str, List[str]], sort_keys: Dict[str, Any]):
        self.progress_bar.hide()
        if searches != self._searches:
            logger.debug(f'{searches=} {extras=} {sort_keys=}')
            self._searches = searches

            if not searches:
                self.list_searches.clear()
                no_results_item = QListWidgetItem('No flippable searches')
                no_results_item.setFlags(Qt.ItemIsEnabled)
                self.list_searches.addItem(no_results_item)
                return

            if extras is None:
                extras = {}

            sorted_searches = sorted(searches.items(), key=lambda guid_name: sort_keys[guid_name[0]])

            prev_selected = self.list_searches.currentItem()
            logger.debug(f'{prev_selected=}')
            if prev_selected:
                prev_selected = prev_selected.data(Qt.UserRole)

            self.list_searches.clear()
            selected = False
            first = True
            for guid, name in sorted_searches:
                if first:
                    first = False
                else:
                    sep_item = QListWidgetItem('')
                    sep_item.setFlags(Qt.ItemIsEnabled)
                    self.list_searches.addItem(sep_item)

                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, guid)
                self.list_searches.addItem(item)
                if guid == prev_selected:
                    selected = True
                    item.setSelected(True)
                if search_extras := extras.get(guid):
                    for extra_str in search_extras:
                        extra_item = QListWidgetItem(extra_str)
                        extra_item.setFlags(extra_item.flags() & ~Qt.ItemIsSelectable)
                        self.list_searches.addItem(extra_item)
            logger.debug(f'{prev_selected=} {selected=}')
            if searches and not selected:
                logger.debug('SET CURRENT ROW 0')
                self.list_searches.setCurrentRow(0)

    def set_progress_bar_visible(self, visible):
        self.progress_bar.setVisible(visible)

    def set_progress(self, flippable, completed, total):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(completed)
        self.progress_bar.setFormat(f'{completed} / {total} ({flippable} flippable)')

    def set_go_handler(self, handler):
        self._connect_signal_to_slot(self.btn_go.clicked, handler)

    def set_cancel_handler(self, handler):
        self._connect_signal_to_slot(self.btn_cancel.clicked, handler)

    def set_copy_handler(self, handler):
        self._connect_signal_to_slot(self.btn_copy.clicked, handler)
