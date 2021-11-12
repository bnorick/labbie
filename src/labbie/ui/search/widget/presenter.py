import itertools
from typing import List, Union

import injector
import loguru

from labbie import bases
from labbie import constants
from labbie import errors
from labbie import mods
from labbie import state
from labbie import result as search_result
from labbie.ui.app import presenter as app
from labbie.ui.search.widget import view
from labbie.ui.result.widget import presenter as result

logger = loguru.logger
_POSITION_FILE = 'position.txt'


class SearchPresenter:

    @injector.inject
    def __init__(
        self,
        constants_: constants.Constants,
        app_state: state.AppState,
        app_presenter: app.AppPresenter,
        bases_: bases.Bases,
        mods_: mods.Mods,
        view: view.SearchWidget,
        result_builder: injector.AssistedBuilder[result.ResultWidgetPresenter]
    ):
        self._constants = constants_
        self._app_state = app_state
        self._app_presenter = app_presenter
        self._bases = bases_
        self._mods = mods_
        self._view = view
        self._result_builder = result_builder

        self._search_id_iter = iter(itertools.count())

        self._view.set_search_mod_handler(self.on_search_mod)
        self._view.set_search_base_handler(self.on_search_base)
        self._view.set_all_handler(self.on_all)
        self._view.set_screen_capture_handler(self.on_screen_capture)

        position = None
        if (position_path := self._constants.data_dir / _POSITION_FILE).is_file():
            with position_path.open('r', encoding='utf8') as f:
                position = [int(val) for val in f.read().split()]
        self._view.set_position(position)
        self._view.set_position_path(position_path)

        # TODO(bnorick): attach to enchants so that we can update the dropdowns when enchants change
        influences = ['Shaper', 'Elder', 'Crusader', 'Redeemer', 'Hunter', 'Warlord']
        self._view.set_influence_options(influences, influences)
        self._view.set_mods(self._mods.helm_display_mods, None)
        self._view.set_bases(self._bases.helm_display_texts)

        if constants_.debug:
            self._view.set_selected_mod('Tornado Shot fires an additional secondary Projectile')

    @property
    def widget(self):
        return self._view

    def reset_position(self):
        self._view.set_position(None)

    def cleanup(self):
        pass

    def populate_view(self, results: Union[None, search_result.Result, List[search_result.Result]],
                      clear=False, switch=False):
        logger.debug(f'{results=}')
        if not results:
            return

        if clear:
            self._view.clear_results()

        if isinstance(results, search_result.Result):
            results = [results]

        for result in results:
            result_presenter = self._result_builder.build()
            result_presenter.populate_view(result)
            tab_title = result.title[:30] + ('...' if len(result.title) > 30 else '')
            self._view.add_result_tab(tab_title, result_presenter.widget, switch=switch)

    def on_search_mod(self, checked):
        try:
            self._app_state.ensure_scrape_enabled()
        except RuntimeError as e:
            self._app_presenter.show(keys.ErrorWindowKey(str(e)))
            return

        mod = self._view.mod

        league_matches = None
        if self._app_state.league_enchants.enabled:
            try:
                league_matches = self._app_state.league_enchants.find_matching_enchants(mod)
            except errors.EnchantsNotLoaded as e:
                self._app_presenter.show(keys.ErrorWindowKey(e))
                return

        daily_matches = None
        try:
            daily_matches = self._app_state.daily_enchants.find_matching_enchants(mod)
        except errors.EnchantsNotLoaded as e:
            self._app_presenter.show(keys.ErrorWindowKey(e))
            return

        result = search_result.Result(
            title=mod,
            search=mod,
            base=False,
            league_result=league_matches,
            daily_result=daily_matches
        )
        self.populate_view(result, switch=True)

    def on_search_base(self, checked):
        try:
            self._app_state.ensure_scrape_enabled()
        except RuntimeError as e:
            self._app_presenter.show(keys.ErrorWindowKey(str(e)))
            return

        base_name = self._view.base
        ilvl = int(self._view.ilvl or 0)
        influences = self._view.influences

        league_matches = None
        if self._app_state.league_enchants.enabled:
            try:
                league_matches = self._app_state.league_enchants.find_matching_bases(base_name, ilvl, influences)
            except errors.EnchantsNotLoaded as e:
                self._app_presenter.show(keys.ErrorWindowKey(e))
                return
            except errors.NoSuchBase:
                league_matches = []

        daily_matches = None
        if self._app_state.daily_enchants.enabled:
            try:
                daily_matches = self._app_state.daily_enchants.find_matching_bases(base_name, ilvl, influences)
            except errors.EnchantsNotLoaded as e:
                self._app_presenter.show(keys.ErrorWindowKey(e))
                return
            except errors.NoSuchBase:
                daily_matches = []

        ilvl = f'i{ilvl}+ ' if ilvl != 0 else ''
        influence = f'{", ".join(influences)} ' if influences else ''
        search = f'{ilvl}{influence}{base_name}'
        result = search_result.Result(
            title=search,
            search=search,
            base=True,
            league_result=league_matches,
            daily_result=daily_matches
        )
        self.populate_view(result, switch=True)

    def on_all(self, checked):
        league_enchants = self._app_state.league_enchants.enchants
        daily_enchants = self._app_state.daily_enchants.enchants

        bases_result = search_result.Result(
            title='Bases',
            search='All Bases',
            base=False,
            league_result=league_enchants,
            daily_result=daily_enchants
        )
        self.populate_view(bases_result)

        enchants_result = search_result.Result(
            title='Enchants',
            search='All Enchants',
            base=True,
            league_result=league_enchants,
            daily_result=daily_enchants
        )
        self.populate_view(enchants_result)

    def on_screen_capture(self, checked):
        self._app_presenter.screen_capture()

    def show(self):
        self._view.show()


from labbie.ui import keys  # noqa: E402
