import collections
import dataclasses
import functools
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import injector
import pyperclip
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from labbie.ui import base
from labbie.ui import clickable_label
from labbie.ui import switch
from labbie.ui import utils

Qt = QtCore.Qt
_LEAGUE_FORMAT = 'League ({})'
_DAILY_FORMAT = 'Daily ({})'
_INDENT = 25


@dataclasses.dataclass
class DisplayResult:
    index: Optional[int] = dataclasses.field(init=False, default=None)
    count: int
    text: str
    data: Any
    indent_level: int = 0
    context_menu_items: Optional[List['ContextMenuItem']] = None

    _displayed_context_menu_indices: Set[int] = dataclasses.field(init=False, default_factory=set)

    def __hash__(self):
        return id(self)

    def context_menu_results_displayed_before(self, index: int):
        return sum(self.context_menu_items[displayed_index]._displayed_result_count
                   for displayed_index in self._displayed_context_menu_indices
                   if displayed_index < index)

    def get_displayable_context_menu_items(self) -> Dict[str, List[Tuple[int, 'ContextMenuItem']]]:
        if not self.context_menu_items:
            return {}

        sections = collections.defaultdict(list)
        for item in self.context_menu_items:
            if item.index in self._displayed_context_menu_indices:
                continue

            sections[item.section].append(item)

        return sections


@dataclasses.dataclass
class ContextMenuItem:
    index: int = dataclasses.field(init=False)
    _displayed_result_count: int = dataclasses.field(init=False, default=0)
    _parent: Optional['ContextMenuItem'] = dataclasses.field(init=False, default=None)
    section: str
    text: str
    display: Union[DisplayResult, List[Union[DisplayResult, 'ContextMenuItem']]]

    def increment_displayed_results(self):
        self._displayed_result_count += 1
        parent = self._parent
        while parent:
            parent._displayed_result_count += 1
            parent = parent._parent

    def set_parent(self, parent: 'ContextMenuItem'):
        self._parent = parent


class ResultWidget(base.BaseWidget):

    @injector.inject
    def __init__(self, parent=None):
        super().__init__(parent)

        self._league_results = None
        self._daily_results = None
        self._current_results = None
        self._results_str = ''

        self.widget_type = QtWidgets.QWidget(self)
        self.toggle_type = switch.Toggle(self.widget_type, thumb_radius=8, track_radius=5)
        self.lbl_league = clickable_label.ClickableLabel(self.widget_type)
        self.lbl_daily = clickable_label.ClickableLabel(self.widget_type)
        self.lbl_title = QtWidgets.QLabel(self)

        self.btn_price_check = QtWidgets.QPushButton('Price Check', self)
        self.btn_copy = QtWidgets.QPushButton('Copy', self)
        self.lbl_selected_stats = QtWidgets.QLabel(self)

        self.stack_results = QtWidgets.QStackedWidget(self)
        self._widget_league_results = None
        self._widget_daily_results = None

        self.lbl_league.setStyleSheet('QLabel { font-weight: bold; }')
        self.lbl_daily.setStyleSheet('QLabel { font-weight: bold; }')
        self.lbl_league.hide()
        self.toggle_type.hide()
        self.lbl_daily.hide()
        self.btn_price_check.setEnabled(False)  # enabled upon selection

        layout_type = QtWidgets.QHBoxLayout()
        layout_type.addWidget(self.lbl_league)
        layout_type.addWidget(self.toggle_type)
        layout_type.addWidget(self.lbl_daily)
        layout_type.addSpacing(15)
        layout_type.setContentsMargins(0, 0, 0, 0)

        self.widget_type.setLayout(layout_type)

        layout_top = QtWidgets.QHBoxLayout()
        layout_top.addWidget(self.widget_type)
        layout_top.addWidget(self.lbl_title, 1)

        layout_right = QtWidgets.QVBoxLayout()
        layout_right.addWidget(self.btn_price_check)
        layout_right.addWidget(self.btn_copy)
        layout_right.addWidget(self.lbl_selected_stats)

        layout = QtWidgets.QGridLayout()
        layout.addLayout(layout_top, 0, 0, 1, 2)
        layout.addWidget(self.stack_results, 1, 0)
        layout.addLayout(layout_right, 1, 1)
        self.setLayout(layout)

        self.toggle_type.toggled.connect(self._on_type_toggled)
        self.lbl_league.clicked.connect(lambda: self.toggle_type.setChecked(False))
        self.lbl_daily.clicked.connect(lambda: self.toggle_type.setChecked(True))
        self.btn_copy.clicked.connect(lambda _: pyperclip.copy(self._results_str))

    def _on_results_selection_changed(self):
        selected = self.stack_results.currentWidget().selectedItems()
        items_selected = bool(selected)
        self.btn_price_check.setEnabled(items_selected)
        # self._update_selected_stats(selected)

    def _on_type_toggled(self, is_daily):
        self._set_active_type(is_daily)
        self._current_results = self._daily_results if is_daily else self._league_results
        widget = self._widget_daily_results if is_daily else self._widget_league_results
        self.stack_results.setCurrentWidget(widget)
        selected = widget.selectedItems()
        items_selected = bool(selected)
        self.btn_price_check.setEnabled(items_selected)
        # self._update_selected_stats(selected)

    def _set_active_type(self, is_daily):
        palette = self.palette()
        inactive = palette.color(palette.ColorGroup.Disabled, palette.ColorRole.Text).name()
        active = palette.text().color().name()
        if is_daily:
            self.lbl_league.setStyleSheet(f'QLabel {{ color: {inactive}; font-weight:bold; }}')
            self.lbl_daily.setStyleSheet(f'QLabel {{ color: {active}; font-weight:bold; }}')
        else:
            self.lbl_league.setStyleSheet(f'QLabel {{ color: {active}; font-weight:bold; }}')
            self.lbl_daily.setStyleSheet(f'QLabel {{ color: {inactive}; font-weight:bold; }}')

    def _show_context_menu(self, point: QtCore.QPoint):
        list_results = self.stack_results.currentWidget()
        item = list_results.itemAt(point)
        row = list_results.row(item)
        result: DisplayResult = item.data(Qt.UserRole)
        menu_items = result.get_displayable_context_menu_items()

        if not menu_items:
            return

        menu = QtWidgets.QMenu(self)
        for section, items in menu_items.items():
            menu.addSection(section)
            for menu_item in items:
                action = menu.addAction(menu_item.text)
                action.triggered.connect(
                    functools.partial(
                        self._add_context_menu_result,
                        source=result,
                        source_row=row,
                        context_menu_index=menu_item.index
                    )
                )
        menu.exec(list_results.mapToGlobal(point))

    def _add_context_menu_result(self, source: DisplayResult, source_row: int, context_menu_index: int):
        context_menu_item = source.context_menu_items[context_menu_index]
        displayed_before = source.context_menu_results_displayed_before(context_menu_index)
        row = source_row + 1 + displayed_before

        if source.indent_level == 0 and not source._displayed_context_menu_indices:
            self._add_space_to_list(index=row)

        if isinstance(context_menu_item.display, DisplayResult):
            self._add_result_to_list(context_menu_item.display, index=row)
            context_menu_item.increment_displayed_results()
        else:
            for result in reversed(context_menu_item.display):
                if isinstance(result, DisplayResult):
                    self._add_result_to_list(result, index=row)
                    context_menu_item.increment_displayed_results()
                else:
                    if result.index not in source._displayed_context_menu_indices:
                        displayed_before = source.context_menu_results_displayed_before(result.index)
                        row = source_row + 1 + displayed_before
                        self._add_result_to_list(result.display, index=row)
                        context_menu_item.increment_displayed_results()
                        source._displayed_context_menu_indices.add(result.index)

        source._displayed_context_menu_indices.add(context_menu_index)

    # def _update_selected_stats(self, selected: List[QtWidgets.QListWidgetItem] = None):
    #     if selected is None:
    #         selected = self.stack_results.currentWidget().selectedItems()

    #     if not selected:
    #         self.lbl_selected_stats.setText('')
    #         return

    #     selected_results = set()
    #     max_selected_subresult_index = collections.defaultdict(int)

    #     for item in selected:
    #         data = item.data(Qt.UserRole)
    #         if data.parent_index is None:
    #             selected_results.add(data.index)
    #         else:
    #             cur_max = max_selected_subresult_index[data.parent_index]
    #             max_selected_subresult_index[data.parent_index] = max(cur_max, data.index)

    #     selected_count = 0
    #     for index in selected_results:
    #         max_selected_subresult_index.pop(index, None)
    #         selected_count += self._current_results[index].count

    #     partial_selections = []
    #     for parent_index, subresult_index in max_selected_subresult_index.items():
    #         parent = self._current_results[parent_index]
    #         count = parent.subresult(subresult_index).count
    #         selected_count += count
    #         partial_selections.append((parent.text, count, parent.count))

    #     if self._current_results is self._league_results:
    #         total = self._total_league_results
    #     else:
    #         total = self._total_daily_results

    #     text = [f'<strong>Total:</strong> {selected_count / total * 100:0.2f}% ({selected_count}/{total})']
    #     for partial_text, partial_count, partial_total in partial_selections:
    #         text.append(f'<strong>{partial_text}:</strong> {partial_count / partial_total * 100:0.2f}% '
    #                     f'({partial_count}/{partial_total})')
    #     text = '<br />'.join(text)
    #     self.lbl_selected_stats.setText(text)

    def set_results(self, title, league_results: Optional[Tuple[int, List[DisplayResult]]],
                    daily_results: Optional[Tuple[int, List[DisplayResult]]], results_str: str,
                    selection_changed_handler: Callable):
        """Sets the results for this widget.

        Args:
            league_results: the results from the league scrape (possibly an empty list) or `None` if
              league_results are not to be shown
            daily_results: the results from the daily scrape (possibly an empty list) or `None` if
              daily_results are not to be shown
        """
        self._results_str = results_str

        self.lbl_title.setText(title)

        if league_results is not None and daily_results is not None:
            self.toggle_type.show()

        if league_results is not None:
            count, self._league_results = league_results
            self.lbl_league.setText(_LEAGUE_FORMAT.format(count))
            self.lbl_league.show()

        if daily_results is not None:
            count, self._daily_results = daily_results
            self.lbl_daily.setText(_DAILY_FORMAT.format(count))
            self.lbl_daily.show()

        results_league, results_daily = self._build_results(self._league_results, self._daily_results, selection_changed_handler=selection_changed_handler)
        self._widget_league_results = results_league
        self._widget_daily_results = results_daily

        if results_league is not None:
            self.stack_results.setCurrentWidget(results_league)
            self._current_results = self._league_results
            self._set_active_type(is_daily=False)
        else:
            self.stack_results.setCurrentWidget(self._widget_daily_results)
            self._current_results = self._daily_results
            self._set_active_type(is_daily=True)

    def _build_results(
        self,
        *results_lists: List[Optional[List[DisplayResult]]],
        selection_changed_handler: Callable = None
    ) -> List[Optional[QtWidgets.QListWidget]]:
        if not results_lists:
            return None

        widgets = []
        for results in results_lists:
            if results is None:
                widgets.append(None)
            else:
                widget = self._build_result_list(results)
                widgets.append(widget)
                self.stack_results.addWidget(widget)
                if selection_changed_handler:
                    self._connect_signal_to_slot(widget.itemSelectionChanged, selection_changed_handler)

        return widgets

    def _build_result_list(self, results: List[DisplayResult]):
        list_results = QtWidgets.QListWidget(self)
        list_results.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        list_results.setContextMenuPolicy(Qt.CustomContextMenu)

        if results:
            for result in results:
                self._add_result_to_list(result, list_results)
        else:
            item = QtWidgets.QListWidgetItem('No results')
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            list_results.addItem(item)

        # list_results.itemDoubleClicked.connect(self._on_item_double_clicked)
        list_results.itemSelectionChanged.connect(self._on_results_selection_changed)
        list_results.customContextMenuRequested.connect(self._show_context_menu)

        return list_results

    def _add_result_to_list(self, result: DisplayResult, list_widget: QtWidgets.QListWidget = None,
                            index=None):
        if list_widget is None:
            list_widget = self.stack_results.currentWidget()

        item_result = QtWidgets.QListWidgetItem()
        item_result.setData(Qt.UserRole, result)

        if index is None:
            list_widget.addItem(item_result)
        else:
            list_widget.insertItem(index, item_result)

        widget_result = QtWidgets.QWidget(self)

        lbl_count = QtWidgets.QLabel(str(result.count), widget_result)
        lbl_count.setMinimumWidth(_INDENT)
        lbl_count.setAlignment(Qt.AlignRight)
        lbl_name = QtWidgets.QLabel(result.text, widget_result)

        layout_result = QtWidgets.QHBoxLayout()
        layout_result.setContentsMargins(0, 0, 0, 0)
        if result.indent_level:
            layout_result.addSpacing(result.indent_level * _INDENT)
        layout_result.addWidget(lbl_count, 0, Qt.AlignmentFlag.AlignRight)
        layout_result.addWidget(lbl_name, 1)
        widget_result.setLayout(layout_result)

        item_result.setSizeHint(widget_result.sizeHint())

        list_widget.setItemWidget(item_result, widget_result)

    def _add_space_to_list(self, list_widget: QtWidgets.QListWidget = None, index=None):
        if list_widget is None:
            list_widget = self.stack_results.currentWidget()

        item = QtWidgets.QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QtCore.QSize(list_widget.sizeHint().width(), 5))

        if index is None:
            list_widget.addItem(item)
        else:
            list_widget.insertItem(index, item)

    def set_selected_stats_text(self, text):
        self.lbl_selected_stats.setText(text)

    def set_price_check_handler(self, handler):
        self._connect_signal_to_slot(self.btn_price_check.clicked, handler)

    def get_selected_data(self):
        return [item.data(Qt.UserRole) for item in self.stack_results.currentWidget().selectedItems()]

    # Properties
    @utils.checkbox_property
    def scrape_type(self):
        return self.toggle_type
