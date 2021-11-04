import asyncio
from loguru import logger
import pyperclip
from sniper.client.ui.searches.widget.presenter import SearchesPresenter
from sniper.common.config import CommonConfig

from sniper.vendor.injector import inject
from sniper.common.search.manager import SearchManager
import sniper.client.ui.app.presenter as app
from .view import FlipAssistantWidget


class FlipAssistantPresenter(SearchesPresenter):
    @inject
    def __init__(self, common_config: CommonConfig, search_manager: SearchManager, app_presenter: 'app.AppPresenter', view: FlipAssistantWidget):
        self._common_config = common_config
        self._search_manager = search_manager

        self._app_presenter = app_presenter
        self._view = view

        self._searches = None
        self._task = None
        self._selected_guids = None

        self._view.set_searches_selected_handler(self.on_searches_selected)
        self._view.set_go_handler(self.on_go)
        self._view.set_cancel_handler(self.on_cancel)
        self._view.set_edit_handler(self.on_edit_signal)
        self._view.set_offer_handler(self.on_offer_signal)
        self._view.set_open_in_browser_handler(self.on_open_in_browser_signal)
        self._view.set_copy_handler(self.on_copy)

    @property
    def widget(self):
        return self._view

    def cleanup(self):
        pass

    def populate_view(self, searches, auto_start):
        self._searches = searches

        if searches:
            self._view.set_subtitle(f'Selected Searches ({len(searches)})')

        if auto_start:
            self.on_go(None)

    def on_searches_selected(self, guids):
        if not guids:
            self._view.set_enabled_buttons(edit=False, offer_unpriced=False, open_in_browser=False)
        else:
            super().on_searches_selected(guids)

    def on_go(self, checked):
        self._view.set_visible_buttons(go=False, cancel=True)
        self._view.set_progress_bar_visible(True)
        if self._task is None:
            # guarding like this may not be necessary, but for safety we will
            logger.debug('STARTING FLIP ASSISTANT')
            self._task = asyncio.create_task(self.run())

    def on_cancel(self, checked):
        if self._task:
            if self._task.done() and self._task.exception:
                logger.exception(self._task.exception)
            else:
                self._task.cancel()
            self._task = None
        self._view.set_visible_buttons(go=True, cancel=False)
        self._view.set_progress_bar_visible(False)

    async def run(self):
        logger.debug('HERE')
        if self._searches is None:
            all_searches = self._search_manager
        else:
            all_searches = self._searches

        logger.debug(f'{len(all_searches)=} {all_searches=}')

        searches = [search for search in all_searches if search.flippable]

        logger.debug(f'{len(searches)=} {searches=}')

        # flip_info_tasks = []
        # for search in searches:
        #     task = asyncio.create_task(search.flip_info())
        #     task.search = search
        #     flip_info_tasks.append(task)

        # total = len(searches)
        # flip_info = {}
        # completed = 0

        # # emulate as_completed with asyncio.wait()
        # while flip_info_tasks:
        #     done, flip_info_tasks = await asyncio.wait(flip_info_tasks, return_when=asyncio.FIRST_COMPLETED)
        #     for t in done:
        #         completed += 1

        #         try:
        #             result = await t
        #             flip_info[t.search] = result
        #         except Exception as e:
        #             print(f'{e} happened while processing {t.search}')

        #         self._view.set_completion_status(completed / total)

        awaitables = []
        for search in searches:
            awaitables.append(search.flip_info())

        total = len(searches)
        completed = 0
        flippable = 0
        self._view.set_progress(flippable, completed, total)

        all_flip_info = {}
        for future in asyncio.as_completed(awaitables):
            flip_info = await future
            if flip_info.flippable:
                flippable += 1
                all_flip_info[flip_info.search] = flip_info
            completed += 1
            self._view.set_progress(flippable, completed, total)

        flippable_searches = {}
        extras = {}
        sort_keys = {}
        for search, flip_info in all_flip_info.items():
            logger.debug(f'flip info for {search}, {flip_info=}')
            guid = search.guid
            cost = flip_info.cost
            value = flip_info.estimated_value
            profit = flip_info.estimated_profit
            flippable_searches[guid] = search.name
            cost_str = f'{int(cost)}' if cost.is_integer() else f'{cost:.2f}'
            if value is None:
                value_str = 'Unknown'
                profit = float('inf')
                profit_str = 'Unknown'
            else:
                value_str = f'{int(value)}' if value.is_integer() else f'{value:.2f}'
                profit = value - cost
                profit_str = f'{int(profit)}' if profit.is_integer() else f'{profit:.2f}'

            extras[guid] = [
                f'Flip range: {cost_str} → {value_str}',
                f'Profit: {profit_str}',
                f'Total listed (online): {flip_info.total}'
            ]
            sort_keys[guid] = profit

        flip_text = []
        for guid, name in flippable_searches.items():
            flip_text.append(f'- {name}')
            for extra_str in extras[guid]:
                flip_text.append(f'  - {extra_str}')
        self._text = '\n'.join(flip_text)

        self._view.set_results(flippable_searches, extras, sort_keys)
        self._view.set_visible_buttons(go=True, cancel=False)

        if flippable_searches:
            self._view.set_enabled_buttons(copy=True)
        else:
            self._view.set_enabled_buttons(copy=False, edit=False, offer_unpriced=False, open_in_browser=False)
        # if not flippable_searches:
        #     self._view.set_enabled_buttons(edit=False, offer_unpriced=False, open_in_browser=False)

    def on_copy(self, checked):
        if text := getattr(self, '_text', None):
            pyperclip.copy(text)

    def show(self):
        self._view.show()
