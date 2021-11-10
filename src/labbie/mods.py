import dataclasses
from logging import log
import string
import functools
from typing import Dict, Optional, Tuple, Union

import injector
import loguru
import datrie

from labbie import resources
from labbie import trade

logger = loguru.logger


@dataclasses.dataclass
class HelmModInfo:
    mod: str
    trade_text: Optional[str]
    trade_stat_id: Optional[str]
    trade_stat_value: Union[None, int, float]


@injector.singleton
class Mods:

    @injector.inject
    def __init__(self, resource_manager: resources.ResourceManager, trade_: trade.Trade):
        self._resource_manager = resource_manager
        self._trade = trade_

        self._raw_mods = resource_manager.mods

        self.helm_mod_info = self._build_helm_mod_info(self._raw_mods['helmet'])  # exact mod -> HelmModInfo

    @functools.cached_property
    def helm_mods(self):
        return sorted(self.helm_mod_info.keys())

    def _build_helm_mod_info(self, mods: Dict[str, Tuple[str, Optional[int]]]) -> Dict[str, HelmModInfo]:
        result = {}
        for mod_format, (slot_patterns, values) in mods.items():
            if '{' not in mod_format:
                trade_text = mod_format.lower()
                result[mod_format] = HelmModInfo(
                    mod=mod_format,
                    trade_text=trade_text,
                    trade_stat_id=self._trade.text_to_stat_id.get(trade_text),
                    trade_stat_value=None
                )
                continue

            # if # ocurrs in mod_format we need to rethink some logic below
            assert '#' not in mod_format

            slotted = mod_format.format(*slot_patterns).lower()
            if slotted in self._trade.text_to_stat_id:
                trade_text = slotted
            elif (hash_only_slotted := mod_format.format('#', '#').lower()) in self._trade.text_to_stat_id:
                trade_text = hash_only_slotted
            else:
                logger.debug(f'Unable to find trade text for {mod_format=} {slotted=} {hash_only_slotted=}')
                trade_text = None

            if len(values) == 1:
                trade_stat_value = values[0]
            elif len(values) == 2:
                trade_stat_value = sum(values) / 2
            else:
                raise ValueError(f'{mod_format=} has an unexpected number of values - {len(values)=} {values=}')

            slot_values = [pattern.replace('#', str(value)) for pattern, value in zip(slot_patterns, values)]
            mod = mod_format.format(*slot_values)
            result[mod] = HelmModInfo(
                mod=mod,
                trade_text=trade_text,
                trade_stat_id=self._trade.text_to_stat_id.get(trade_text),
                trade_stat_value=trade_stat_value
            )
        return result

    @functools.cached_property
    def mod_trie(self) -> datrie.Trie:
        logger.debug('Creating Trie')
        trie = datrie.Trie(string.printable)
        for mod in self.helm_mods:
            trie[mod] = 1
        logger.debug(f'{len(trie)}, trie length')
        return trie

    def get_mod_list_from_ocr_results(self, enchant_list):
        trie = self.mod_trie
        logger.debug(f'{enchant_list}')
        full_enchants = []
        potential_enchants = []
        for partial_enchant in enchant_list:
            if partial_enchant == '':
                continue
            partial_enchant = partial_enchant.replace('’', "'")
            # continuation of enchant
            if potential_enchants:
                is_partial_enchant = False
                reduced_potential_enchants = []
                for enchant in potential_enchants:
                    if partial_enchant in enchant:
                        reduced_potential_enchants.append(enchant)
                        logger.debug(f'partial part of previous {partial_enchant=}')
                        if enchant not in full_enchants:
                            full_enchants.append(enchant)
                        is_partial_enchant = True
                potential_enchants = reduced_potential_enchants
                if is_partial_enchant:
                    continue
                # multiple potential enchants still, but the extras will be filtered out
                # when doing comparison against the trade searches.
                if len(potential_enchants) > 1:
                    full_enchants.extend(potential_enchants)
            potential_enchants = trie.keys(partial_enchant)
            logger.debug(f'found potential enchant: {potential_enchants}')

            if len(potential_enchants) == 1:
                full_enchants.extend(potential_enchants)

        if len(potential_enchants) > 1:
            full_enchants.extend(potential_enchants)
        logger.info(f'found {full_enchants=}')
        return full_enchants
