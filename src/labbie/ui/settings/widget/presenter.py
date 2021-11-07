import asyncio

import injector
import loguru

from labbie import config
from labbie import constants
from labbie import state
from labbie.ui.app import presenter as app
from labbie.ui.settings.widget import view
from labbie.ui.screen_selection.widget import view as screen_selection

logger = loguru.logger
_Config = config.Config
_Constants = constants.Constants


class SettingsPresenter:

    @injector.inject
    def __init__(
        self,
        constants: _Constants,
        app_state: state.AppState,
        app_presenter: app.AppPresenter,
        config: _Config,
        view: view.SettingsWidget,
        screen_selection_view_builder: injector.AssistedBuilder[screen_selection.ScreenSelectionWidget]
    ):
        self._constants = constants
        self._app_state = app_state
        self._app_presenter = app_presenter
        self._config = config
        self._view = view
        self._screen_selection_view_builder = screen_selection_view_builder

        self._view.set_select_bounds_handler(self.on_select_bounds)
        self._view.set_save_handler(self.on_save)

        self._view.league = self._config.league
        self._view.daily = self._config.daily
        self._view.clear_previous = self._config.ocr.clear_previous
        self._view.hotkey = self._config.ui.hotkeys.ocr
        self._view.left = str(self._config.ocr.bounds.left)
        self._view.top = str(self._config.ocr.bounds.top)
        self._view.right = str(self._config.ocr.bounds.right)
        self._view.bottom = str(self._config.ocr.bounds.bottom)

    @property
    def widget(self):
        return self._view

    def on_select_bounds(self, checked):
        self._screen_selection_view = self._screen_selection_view_builder.build(
            left=int(self._view.left),
            top=int(self._view.top),
            right=int(self._view.right),
            bottom=int(self._view.bottom)
        )
        self._screen_selection_view.set_done_handler(self.on_screen_selection_done)
        self._screen_selection_view.show()

    def on_screen_selection_done(self):
        self._screen_selection_view.hide()
        left, top, right, bottom = self._screen_selection_view.get_position()
        self._view.left = str(left)
        self._view.top = str(top)
        self._view.right = str(right)
        self._view.bottom = str(bottom)

    async def on_save(self, checked):
        if self._view.league != self._config.league:
            self._config.league = self._view.league
            if self._config.league:
                asyncio.create_task(self._app_state.league_enchants.download_or_load(self._constants))
            else:
                self._app_state.league_enchants.set_enchants(None, None)

        if self._view.daily != self._config.daily:
            self._config.daily = self._view.daily
            if self._config.daily:
                asyncio.create_task(self._app_state.daily_enchants.download_or_load(self._constants))
            else:
                self._app_state.daily_enchants.set_enchants(None, None)

        if self._view.hotkey != self._config.ui.hotkeys.ocr:
            self._config.ui.hotkeys.ocr = self._view.hotkey
            self._config.ui.hotkeys.notify(ocr=self._view.hotkey)
        self._config.ocr.clear_previous = self._view.clear_previous
        self._config.ocr.bounds.left = int(self._view.left)
        self._config.ocr.bounds.top = int(self._view.top)
        self._config.ocr.bounds.right = int(self._view.right)
        self._config.ocr.bounds.bottom = int(self._view.bottom)
        self._config.save()
        self._view.close()

    def cleanup(self):
        self._screen_selection_view.close()

    # def populate_view(self, results: Union[None, search_result.Result, List[search_result.Result]], base=False):
    #     logger.debug(f'{results=}')
    #     if not results:
    #         return

    #     if isinstance(results, search_result.Result):
    #         results = [results]

    #     summarizer = enchants.enchant_summary if not base else enchants.base_summary

    #     for result in results:
    #         result_presenter = self._result_builder.build()

    #         league_result = []
    #         if result.league_result is not None:
    #             league_result.append(f'LEAGUE ({len(result.league_result)})')
    #             league_result.append(summarizer(result.league_result))
    #         league_result = '\n'.join(league_result) or None

    #         daily_result = []
    #         if result.daily_result is not None:
    #             daily_result.append(f'DAILY ({len(result.daily_result)})')
    #             daily_result.append(summarizer(result.daily_result))
    #         daily_result = '\n'.join(daily_result) or None

    #         result_presenter.populate_view(result.search, league_result, daily_result)
    #         title = result.title[:30] + ('...' if len(result.title) > 30 else '')
    #         self._view.add_result(title, result_presenter.widget)

    # def on_enchants_changed(self, val):
    #     logger.info(f'ENCHANTS CHANGED type={val.type if val else None}')
    #     app_state = self._app_state

    #     if (app_state.league_enchants.state is not enchants.State.LOADED
    #             and app_state.daily_enchants.state is not enchants.State.LOADED):
    #         return

    #     mods = set()
    #     if app_state.league_enchants:
    #         try:
    #             mods.update(app_state.league_enchants.mods)
    #         except errors.EnchantsNotLoaded:
    #             pass
    #     if app_state.daily_enchants:
    #         try:
    #             mods.update(app_state.daily_enchants.mods)
    #         except errors.EnchantsNotLoaded:
    #             pass

    #     self._mod_to_unexact_mod = {}
    #     self._unexact_mod_to_mod = {}
    #     highest_mod = {}
    #     for mod in mods:
    #         unexact = enchants.unexact_mod(mod)
    #         self._mod_to_unexact_mod[mod] = unexact

    #         if mod > highest_mod.get(unexact, ''):
    #             highest_mod[unexact] = mod
    #             self._unexact_mod_to_mod[unexact] = mod

    #     sortable_mods = [(self._mod_to_unexact_mod[mod], mod) for mod in mods]
    #     unexact_mods, mods = zip(*sorted(sortable_mods, key=lambda x: (x[0].lower(), x[1].lower())))
    #     self._mods = mods
    #     self._unexact_mods = list(dict.fromkeys(unexact_mods))  # deduplicates the list

    #     bases = set()
    #     if app_state.league_enchants:
    #         try:
    #             bases.update(app_state.league_enchants.bases)
    #         except errors.EnchantsNotLoaded:
    #             pass
    #     if app_state.daily_enchants:
    #         try:
    #             bases.update(app_state.daily_enchants.bases)
    #         except errors.EnchantsNotLoaded:
    #             pass
    #     self._bases = sorted(bases)

    #     if self._view.exact_mod:
    #         self._view.set_mods(self._mods, None)
    #     else:
    #         self._view.set_mods(self._unexact_mods, None)
    #     self._view.set_bases(self._bases)

    # def on_exact_mod(self, checked):
    #     mods = self._mods if checked else self._unexact_mods
    #     equivalent_mods = self._unexact_mod_to_mod if checked else self._mod_to_unexact_mod
    #     self._view.set_mods(mods, equivalent_mods)

    # def on_search_mod(self, checked):
    #     mod = self._view.mod

    #     league_matches = None
    #     try:
    #         league_matches = self._app_state.league_enchants.find_matching_enchants(mod)
    #     except errors.EnchantsNotLoaded:
    #         pass

    #     daily_matches = None
    #     try:
    #         daily_matches = self._app_state.daily_enchants.find_matching_enchants(mod)
    #     except errors.EnchantsNotLoaded:
    #         pass

    #     result = search_result.Result(title=mod, search=mod, league_result=league_matches, daily_result=daily_matches)
    #     self.populate_view(result)

    # def on_search_base(self, checked):
    #     base_name = self._view.base
    #     ilvl = int(self._view.ilvl or 0)
    #     influences = self._view.influences

    #     league_matches = None
    #     try:
    #         league_matches = self._app_state.league_enchants.find_matching_bases(base_name, ilvl, influences)
    #     except (errors.EnchantsNotLoaded, errors.NoSuchBase):
    #         pass

    #     daily_matches = None
    #     try:
    #         daily_matches = self._app_state.daily_enchants.find_matching_bases(base_name, ilvl, influences)
    #     except (errors.EnchantsNotLoaded, errors.NoSuchBase):
    #         pass

    #     search = []
    #     if ilvl != 0:
    #         search.append(f'{ilvl}+')
    #     if influences:
    #         search.append(', '.join(influences))
    #     search.append(base_name)
    #     search = ' '.join(search)

    #     result = search_result.Result(title=search, search=search, league_result=league_matches, daily_result=daily_matches)
    #     self.populate_view(result, base=True)

    # def on_all(self, checked):
    #     league_matches = self._app_state.league_enchants.enchants
    #     daily_matches = self._app_state.daily_enchants.enchants

    #     bases = search_result.Result(title='Bases', search='All Bases', league_result=league_matches, daily_result=daily_matches)
    #     self.populate_view(bases)

    #     enchants = search_result.Result(title='Enchants', search='All Enchants', league_result=league_matches, daily_result=daily_matches)
    #     self.populate_view(enchants, base=True)

    # def on_screen_capture(self, checked):
    #     self._app_presenter.screen_capture(self._view.exact_screen_capture)

    def show(self):
        self._view.show()
