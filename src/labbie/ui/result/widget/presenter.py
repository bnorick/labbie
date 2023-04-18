import base64
import collections
import dataclasses
import json
from urllib import parse
import webbrowser
from typing import List, Optional

import injector
import loguru

from labbie import bases
from labbie import constants
from labbie import enchants
from labbie import mods
from labbie import result
from labbie.ui.result.widget import view

logger = loguru.logger
_HTML_PAYLOAD_FORMAT = '''<html>
<body>
<h1>Trade Rate Limit Protection</h1>
<h3>You will be redirected to your search for {search} in <span id="seconds"></span> seconds.</h3>
At the <strong>risk of being rate limited</strong>, you can click <a href="{url}">here</a> to proceed now.

<style>
body {{
    background-color: rgb(53, 53, 53);
    color: rgb(180, 180, 180);
}}
a {{
    color: rgb(56, 252, 196);
}}
</style>
<script>
    var delay = {delay};

    function decrement() {{
        if (delay <= 0) {{
            window.location = "{url}";
            return;
        }}

        document.getElementById('seconds').innerText = Math.floor(delay);
        delay -= .25;
        setTimeout(decrement, 250);
    }}

    decrement();
</script>
</body>
</html>
'''
_MAX_ILVL = 100
_MAX_DISPLAY_ILVL = 86


@dataclasses.dataclass
class ResultData:
    name: str
    base: str
    unique: bool
    ilvl: Optional[int]
    influence: Optional[str]

    def __str__(self):
        ilvl = f'i{self.ilvl}+ ' if self.ilvl else ''
        influence = f'{self.influence} ' if self.influence and self.influence != 'Uninfluenced' else ''
        base = self.base
        return f'{ilvl}{influence}{base}'

    def build_search_url(self, enchant_stat_id, enchant_stat_value):
        stats = [
            {
                'type': 'and',
                'filters': [{'id': enchant_stat_id}]
            }
        ]
        if enchant_stat_value is not None:
            stats[0]['filters'][0].update(
                min=enchant_stat_value,
                max=enchant_stat_value
            )

        query = {
            'status': {
                'option': 'online'
            },
            'stats': stats,
            'type': self.base
        }

        search = {
            'query': query,
            'sort': {
                'price': 'asc'
            }
        }

        query_filters = {}

        if self.unique:
            query['name'] = self.name
        else:
            query_filters['type_filters'] = {
                'filters': {
                    'rarity': {
                        'option': 'nonunique'
                    }
                }
            }

        if self.ilvl:
            query_filters['misc_filters'] = {
                'filters': {
                    'ilvl': {
                        'min': self.ilvl
                    }
                }
            }

        if self.influence and self.influence != 'Uninfluenced':
            influences = [inf.lower() for inf in self.influence.split(', ')]
            stats[0]['filters'].extend({'id': f'pseudo.pseudo_has_{influence}_influence'} for influence in influences)

        if query_filters:
            query['filters'] = query_filters

        query_string = parse.urlencode({'q': json.dumps(search)}, quote_via=parse.quote)
        return f'https://www.pathofexile.com/trade/search/Scourge?{query_string}'

    def price_check_url(self, enchant_stat_id, enchant_value, delay=0):
        search_url = self.build_search_url(enchant_stat_id, enchant_value)
        logger.debug(f'{search_url=}')
        html = _HTML_PAYLOAD_FORMAT.format(delay=delay, url=search_url, search=self)
        payload = base64.b64encode(html.encode('utf8'))
        return 'https://labbie-redirect.azurewebsites.net/' + payload.decode('utf8')


class ResultWidgetPresenter:

    @injector.inject
    def __init__(self, constants_: constants.Constants, bases_: bases.Bases, mods_: mods.Mods, view: view.ResultWidget):
        self._constants = constants_
        self._bases = bases_
        self._mods = mods_
        self._view = view

        self._mod = None

        # NOTE: connecting the clicked signal to self.on_price_check directly as the slot wasn't working
        # for some reason, no clue.
        self._view.set_price_check_handler(lambda: self.on_price_check())

        self._show_hints = None

    @property
    def widget(self):
        return self._view

    def populate_view(self, result: result.Result):
        self._mod = result.search

        league_results = None
        if result.league_result is not None:
            if result.base:
                league_results = self._build_base_search_display_results(result.league_result)
            else:
                league_results = self._build_enchant_search_display_results(result.league_result)

        daily_results = None
        if result.daily_result is not None:
            if result.base:
                daily_results = self._build_base_search_display_results(result.daily_result)
            else:
                daily_results = self._build_enchant_search_display_results(result.daily_result)

        result_str = result.league_summary(result.base) or ''
        if result_str:
            result_str += '\n\n'
        result_str += result.daily_summary(result.base)

        if result.base:
            self._view.set_price_check_visible(False)
        else:
            self._show_hints = not (self._constants.data_dir / 'result_hints_shown').exists()

        self._view.set_results(
            result.search,
            league_results,
            daily_results,
            results_str=result_str,
            selection_changed_handler=self.on_selection_changed
        )

    def _build_influence_context_menu_items(self, base: str, enchants: List[enchants.Enchant],
                                            ilvl: Optional[int] = None):
        grouped = collections.defaultdict(list)
        for enchant in enchants:
            grouped[', '.join(enchant.influences) or 'Uninfluenced'].append(enchant)

        context_menu_items = []
        sorted_groups = sorted(grouped.items(), key=lambda e: len(e[1]), reverse=True)
        show_all_extras = []
        for influence, influence_enchants in sorted_groups:
            if len(influence_enchants) > 10:
                # Show explicit context menu items above some threshold
                sub_context_menu_items = None
                if not ilvl:
                    sub_context_menu_items = self._build_ilvl_context_menu_items(
                        base, influence_enchants, influence=influence)

                count = len(influence_enchants)
                display_result = view.DisplayResult(
                    count=count,
                    text=influence,
                    data=ResultData(name=base, base=base, unique=False, ilvl=ilvl, influence=influence),
                    indent_level=2 if ilvl else 1,
                    context_menu_items=sub_context_menu_items
                )

                context_menu_items.append(
                    view.ContextMenuItem(
                        section='Influence',
                        text=f'{len(influence_enchants):>5} {influence}',
                        display=display_result
                    )
                )

                if sub_context_menu_items:
                    parent = context_menu_items[-1]
                    for item in sub_context_menu_items:
                        item.set_parent(parent)
            else:
                # Collect the rest into a "Show all" context menu item
                sub_context_menu_items = None
                if not ilvl:
                    sub_context_menu_items = self._build_ilvl_context_menu_items(
                        base, influence_enchants, influence=influence)

                count = len(influence_enchants)
                display_result = view.DisplayResult(
                    count=count,
                    text=influence,
                    data=ResultData(name=base, base=base, unique=False, ilvl=ilvl, influence=influence),
                    indent_level=2 if ilvl else 1,
                    context_menu_items=sub_context_menu_items
                )
                show_all_extras.append(display_result)

        if show_all_extras:
            context_menu_items.append(
                view.ContextMenuItem(
                    section='Influence',
                    text='Show All',
                    display=context_menu_items + show_all_extras
                )
            )

            for display_result in show_all_extras:
                if display_result.context_menu_items:
                    parent = context_menu_items[-1]
                    for item in display_result.context_menu_items:
                        item.set_parent(parent)

        for index, item in enumerate(context_menu_items):
            item.index = index

        return context_menu_items

    def _build_ilvl_context_menu_items(self, base: str, enchants: List[enchants.Enchant],
                                       influence: Optional[str] = None):
        total = len(enchants)
        grouped = collections.defaultdict(list)
        for enchant in enchants:
            grouped[enchant.ilvl].append(enchant)

        ilvl_count = len(grouped)
        context_menu_items = []

        covered_enchants = []
        for ilvl in range(_MAX_ILVL, _MAX_DISPLAY_ILVL - 1, -1):
            if ilvl_enchants := grouped.get(ilvl):
                covered_enchants.extend(ilvl_enchants)
                ilvl_count -= 1  # combining ilvls about max into max reduces count

        if covered_enchants:
            sub_context_menu_items = None
            if not influence:
                sub_context_menu_items = self._build_influence_context_menu_items(
                    base, covered_enchants, ilvl=ilvl)
            count = len(covered_enchants)
            context_menu_items.append(
                view.ContextMenuItem(
                    section='Item Level',
                    text=f'{count / total * 100:>3.0f}% i{_MAX_DISPLAY_ILVL}+',
                    display=view.DisplayResult(
                        count=count,
                        text=f'i{_MAX_DISPLAY_ILVL}+',
                        data=ResultData(name=base, base=base, unique=False, ilvl=_MAX_DISPLAY_ILVL, influence=influence),
                        indent_level=2 if influence else 1,
                        context_menu_items=sub_context_menu_items
                    )
                )
            )

            if sub_context_menu_items:
                parent = context_menu_items[-1]
                for item in sub_context_menu_items:
                    item.set_parent(parent)

        cumulative_total = len(covered_enchants)
        for ilvl in range(_MAX_DISPLAY_ILVL - 1, 0, -1):
            if (ilvl_enchants := grouped.get(ilvl)) is None:
                continue

            if len(context_menu_items) == 5:
                break
            elif len(context_menu_items) == ilvl_count:
                break

            cumulative_total += len(ilvl_enchants)
            covered_enchants.extend(ilvl_enchants)

            sub_context_menu_items = None
            if not influence:
                sub_context_menu_items = self._build_influence_context_menu_items(
                    base, covered_enchants, ilvl=ilvl)

            context_menu_items.append(
                view.ContextMenuItem(
                    section='Item Level',
                    text=f'{cumulative_total / total * 100:>3.0f}% i{ilvl}+',
                    display=view.DisplayResult(
                        count=cumulative_total,
                        text=f'i{ilvl}+',
                        data=ResultData(name=base, base=base, unique=False, ilvl=ilvl, influence=influence),
                        indent_level=2 if influence else 1,
                        context_menu_items=sub_context_menu_items
                    )
                )
            )

            if sub_context_menu_items:
                parent = context_menu_items[-1]
                for item in sub_context_menu_items:
                    item.set_parent(parent)

        if len(context_menu_items) < ilvl_count:
            show_all_extras = []
            for ilvl in range(ilvl, 0, -1):
                if (ilvl_enchants := grouped.get(ilvl)) is None:
                    continue

                cumulative_total += len(ilvl_enchants)
                covered_enchants.extend(ilvl_enchants)

                sub_context_menu_items = None
                if not influence:
                    sub_context_menu_items = self._build_influence_context_menu_items(
                        base, covered_enchants, ilvl=ilvl)

                show_all_extras.append(
                    view.DisplayResult(
                        count=cumulative_total,
                        text=f'i{ilvl}+',
                        data=ResultData(name=base, base=base, unique=False, ilvl=ilvl, influence=influence),
                        indent_level=2 if influence else 1,
                        context_menu_items=sub_context_menu_items
                    )
                )

            context_menu_items.append(
                view.ContextMenuItem(
                    section='Item Level',
                    text='Show All',
                    display=context_menu_items + show_all_extras
                )
            )

            for display_result in show_all_extras:
                if display_result.context_menu_items:
                    parent = context_menu_items[-1]
                    for item in display_result.context_menu_items:
                        item.set_parent(parent)

        for index, item in enumerate(context_menu_items):
            item.index = index

        return context_menu_items

    def _build_context_menu_items(self, base: str, enchants: List[enchants.Enchant]):
        context_menu_items = []
        context_menu_items.extend(self._build_influence_context_menu_items(base, enchants))
        context_menu_items.extend(self._build_ilvl_context_menu_items(base, enchants))

        for index, item in enumerate(context_menu_items):
            item.index = index

        return context_menu_items

    def _build_base_search_display_results(self, results: List[enchants.Enchant]):
        enchants = collections.Counter()

        for enchant in results:
            for mod in enchant.mods:
                if mod not in self._mods.helm_enchants:
                    continue
                enchants[mod] += 1

        display_results = []
        for index, (enchant, count) in enumerate(enchants.most_common()):
            display_result = view.DisplayResult(
                count=count,
                text=enchant,
                data=None
            )
            display_result.index = index  # this is not a constructor arg, needs to be set here
            display_results.append(display_result)

        return (len(results), display_results)

    def on_price_check(self):
        mod_info = self._mods.helm_enchant_info.get(self._mod)
        if mod_info is None:
            logger.error(f'Unable to find helm mod info for "{self._mod}"')
            return

        if mod_info.trade_stat_id is None:
            logger.error(f'No trade stat id for "{self._mod}" {mod_info=}')
            return

        selected: List[view.DisplayResult] = self._view.get_selected_data()
        delay = 0
        for index, result in enumerate(selected):
            delay = index // 3 * 5.25
            webbrowser.open_new_tab(result.data.price_check_url(mod_info.trade_stat_id, mod_info.trade_stat_value, delay))

    def _build_enchant_search_display_results(self, results: List[enchants.Enchant]):
        all_bases = collections.Counter()
        rare_bases = collections.defaultdict(list)

        for enchant in results:
            all_bases[enchant.display_name] += 1
            if not enchant.unique:
                rare_bases[enchant.item_base].append(enchant)

        display_results = []
        for index, (base, count) in enumerate(all_bases.most_common()):
            context_menu_items = None
            if enchants := rare_bases.get(base):
                context_menu_items = self._build_context_menu_items(base, enchants)

            unique = base not in rare_bases
            # krangle the base so that uniques get the actual base type here
            krangled_base = self._bases.helms[base].base if unique else base
            display_result = view.DisplayResult(
                count=count,
                text=base,
                data=ResultData(name=base, base=krangled_base, unique=unique, ilvl=None, influence=None),
                context_menu_items=context_menu_items
            )
            display_result.index = index  # this is not a constructor arg, needs to be set here
            display_results.append(display_result)

        return (len(results), display_results)

    def on_price_check(self):
        mod_info = self._mods.helm_enchant_info.get(self._mod)
        if mod_info is None:
            logger.error(f'Unable to find helm mod info for "{self._mod}"')
            return

        if mod_info.trade_stat_id is None:
            logger.error(f'No trade stat id for "{self._mod}" {mod_info=}')
            return

        selected: List[view.DisplayResult] = self._view.get_selected_data()
        delay = 0
        for index, result in enumerate(selected):
            delay = index // 3 * 5.25
            webbrowser.open_new_tab(result.data.price_check_url(mod_info.trade_stat_id, mod_info.trade_stat_value, delay))

    def on_selection_changed(self):
        if self._show_hints:
            self._view.show_right_click_hint()
            (self._constants.data_dir / 'result_hints_shown').touch()
            self._show_hints = False
        # selected = self._view.get_selected_data()

        # if not selected:
        #     self._view.set_selected_stats_text('')
        #     return

        # selected_results = set()
        # max_selected_subresult_index = collections.defaultdict(int)

        # for item in selected:
        #     data = item.data(Qt.UserRole)
        #     if data.parent_index is None:
        #         selected_results.add(data.index)
        #     else:
        #         cur_max = max_selected_subresult_index[data.parent_index]
        #         max_selected_subresult_index[data.parent_index] = max(cur_max, data.index)

        # selected_count = 0
        # for index in selected_results:
        #     max_selected_subresult_index.pop(index, None)
        #     selected_count += self._current_results[index].count

        # partial_selections = []
        # for parent_index, subresult_index in max_selected_subresult_index.items():
        #     parent = self._current_results[parent_index]
        #     count = parent.subresult(subresult_index).count
        #     selected_count += count
        #     partial_selections.append((parent.text, count, parent.count))

        # if self._current_results is self._league_results:
        #     total = self._total_league_results
        # else:
        #     total = self._total_daily_results

        # text = [f'<strong>Total:</strong> {selected_count / total * 100:0.2f}% ({selected_count}/{total})']
        # for partial_text, partial_count, partial_total in partial_selections:
        #     text.append(f'<strong>{partial_text}:</strong> {partial_count / partial_total * 100:0.2f}% '
        #                 f'({partial_count}/{partial_total})')
        # text = '<br />'.join(text)
        # self.lbl_selected_stats.setText(text)

    def show(self):
        self._view.show()
