import itertools
from typing import List, Union

import injector
import loguru

from labbie import enchants
from labbie import errors
from labbie import state
from labbie import result as search_result
from labbie.ui.app import presenter as app
from labbie.ui.search.widget import view
from labbie.ui.result.widget import presenter as result

logger = loguru.logger


class SearchPresenter:

    @injector.inject
    def __init__(
        self,
        app_state: state.AppState,
        app_presenter: app.AppPresenter,
        view: view.SearchWidget,
        result_builder: injector.AssistedBuilder[result.ResultWidgetPresenter]
    ):
        self._app_state = app_state
        self._app_presenter = app_presenter
        self._view = view
        self._result_builder = result_builder

        self._search_id_iter = iter(itertools.count())

        self._view.set_search_mod_handler(self.on_search_mod)
        self._view.set_exact_mod_handler(self.on_exact_mod)
        self._view.set_search_base_handler(self.on_search_base)
        self._view.set_all_handler(self.on_all)
        self._view.set_screen_capture_handler(self.on_screen_capture)

        self._mods = []
        self._unexact_mods = []
        self._bases = []

        app_state.league_enchants.attach(self, self.on_enchants_changed, to='enchants')
        app_state.daily_enchants.attach(self, self.on_enchants_changed, to='enchants')

        # TODO(bnorick): attach to enchants so that we can update the dropdowns when enchants change
        influences = ['Shaper', 'Elder', 'Crusader', 'Redeemer', 'Hunter', 'Warlord']
        self._view.set_influence_options(influences, influences)
        self._view.set_mods([''], None)
        self._view.set_bases([''])

        self.on_enchants_changed(app_state.league_enchants)

    @property
    def widget(self):
        return self._view

    def cleanup(self):
        pass

    def populate_view(self, results: Union[None, search_result.Result, List[search_result.Result]],
                      clear=False, base=False):
        logger.debug(f'{results=}')
        if not results:
            return

        if clear:
            self._view.clear_results()

        if isinstance(results, search_result.Result):
            results = [results]

        summarizer = enchants.enchant_summary if not base else enchants.base_summary

        for result in results:
            result_presenter = self._result_builder.build()

            league_result = []
            if result.league_result is not None:
                league_result.append(f'LEAGUE ({len(result.league_result)})')
                league_result.append(summarizer(result.league_result))
            league_result = '\n'.join(league_result) or None

            daily_result = []
            if result.daily_result is not None:
                daily_result.append(f'DAILY ({len(result.daily_result)})')
                daily_result.append(summarizer(result.daily_result))
            daily_result = '\n'.join(daily_result) or None

            result_presenter.populate_view(result.search, league_result, daily_result)
            title = result.title[:30] + ('...' if len(result.title) > 30 else '')
            self._view.add_result(title, result_presenter.widget)

    def on_enchants_changed(self, val):
        app_state = self._app_state

        logger.debug(f'{app_state.league_enchants.state=} {app_state.daily_enchants.state=}')

        if (app_state.league_enchants.state is enchants.State.DISABLED
                and app_state.daily_enchants.state is enchants.State.DISABLED):
            self._view.set_mods([''], None)
            self._view.set_bases([''])
            return

        mods = set()
        if app_state.league_enchants:
            try:
                mods.update(app_state.league_enchants.mods)
            except errors.EnchantsNotLoaded:
                pass
        if app_state.daily_enchants:
            try:
                mods.update(app_state.daily_enchants.mods)
            except errors.EnchantsNotLoaded:
                pass

        self._mod_to_unexact_mod = {}
        self._unexact_mod_to_mod = {}
        highest_mod = {}
        for mod in mods:
            unexact = enchants.unexact_mod(mod)
            self._mod_to_unexact_mod[mod] = unexact

            if mod > highest_mod.get(unexact, ''):
                highest_mod[unexact] = mod
                self._unexact_mod_to_mod[unexact] = mod

        sortable_mods = [(self._mod_to_unexact_mod[mod], mod) for mod in mods]
        unexact_mods, mods = zip(*sorted(sortable_mods, key=lambda x: (x[0].lower(), x[1].lower())))
        self._mods = mods
        self._unexact_mods = list(dict.fromkeys(unexact_mods))  # deduplicates the list

        bases = set()
        if app_state.league_enchants:
            try:
                bases.update(app_state.league_enchants.bases)
            except errors.EnchantsNotLoaded:
                pass
        if app_state.daily_enchants:
            try:
                bases.update(app_state.daily_enchants.bases)
            except errors.EnchantsNotLoaded:
                pass
        self._bases = sorted(bases)

        logger.debug(f'{len(self._mods)=} {len(self._bases)=}')

        if self._view.exact_mod:
            self._view.set_mods(self._mods, None)
        else:
            self._view.set_mods(self._unexact_mods, None)
        self._view.set_bases(self._bases)

        logger.debug(f'{self._view.combo_mod.count()=}')
        logger.debug(f'{self._view.combo_base.count()=}')

    def on_exact_mod(self, checked):
        mods = self._mods if checked else self._unexact_mods
        equivalent_mods = self._unexact_mod_to_mod if checked else self._mod_to_unexact_mod
        self._view.set_mods(mods, equivalent_mods)

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

        result = search_result.Result(title=mod, search=mod, league_result=league_matches, daily_result=daily_matches)
        self.populate_view(result)

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

        search = []
        if ilvl != 0:
            search.append(f'{ilvl}+')
        if influences:
            search.append(', '.join(influences))
        search.append(base_name)
        search = ' '.join(search)

        result = search_result.Result(title=search, search=search, league_result=league_matches, daily_result=daily_matches)
        self.populate_view(result, base=True)

    def on_all(self, checked):
        league_enchants = self._app_state.league_enchants.enchants
        daily_enchants = self._app_state.daily_enchants.enchants

        bases = search_result.Result(title='Bases', search='All Bases', league_result=league_enchants, daily_result=daily_enchants)
        self.populate_view(bases)

        enchants = search_result.Result(title='Enchants', search='All Enchants', league_result=league_enchants, daily_result=daily_enchants)
        self.populate_view(enchants, base=True)

    def on_screen_capture(self, checked):
        self._app_presenter.screen_capture(self._view.exact_screen_capture)

    def show(self):
        self._view.show()


from labbie.ui import keys  # noqa: E402
