import collections
import dataclasses
from logging import log
import string
import functools
from typing import Dict, List, Optional, Tuple, Union

import injector
import loguru
import datrie

from labbie import resources
from labbie import trade

logger = loguru.logger


@dataclasses.dataclass
class HelmModInfo:
    display: bool
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

    @functools.cached_property
    def helm_display_mods(self):
        return sorted(k for k, v in self.helm_mod_info.items() if v.display)

    def _build_helm_mod_info(
        self,
        mods: List[List[Tuple[str, List[str], List[Union[int, str]]]]]
    ) -> Dict[str, HelmModInfo]:
        result = {}
        for index, mod_variants in enumerate(mods):
            trade_text = None
            matched_index = None

            for variant_index, (mod_format, slot_patterns, _) in enumerate(mod_variants):
                if '{' not in mod_format:
                    candidate = mod_format.lower()
                    if candidate in self._trade.text_to_stat_id:
                        trade_text = candidate
                        matched_index = variant_index
                        break

                slotted = mod_format.format(*slot_patterns).lower()
                hash_only_slot_patterns = ['#'] * mod_format.count('{')
                hash_only_slotted = mod_format.format(*hash_only_slot_patterns).lower()
                if slotted in self._trade.text_to_stat_id:
                    trade_text = slotted
                    matched_index = variant_index
                    break
                elif hash_only_slotted in self._trade.text_to_stat_id:
                    trade_text = hash_only_slotted
                    matched_index = variant_index
                    break
                else:
                    continue
            else:
                logger.warning(f'No trade text found for {index=} {mod_variants=}')

            trade_stat_id = self._trade.text_to_stat_id.get(trade_text)
            for variant_index, (mod_format, slot_patterns, values) in enumerate(mod_variants):
                if '{' not in mod_format:
                    result[mod_format] = HelmModInfo(
                        display=(variant_index == matched_index),
                        mod=mod_format,
                        trade_text=trade_text,
                        trade_stat_id=trade_stat_id,
                        trade_stat_value=None
                    )
                    continue

                # if # ocurrs in mod_format we need to rethink some logic below
                assert '#' not in mod_format

                if len(values) == 1:
                    trade_stat_value = values[0]
                elif len(values) == 2:
                    trade_stat_value = sum(values) / 2
                else:
                    raise ValueError(f'{mod_format=} has an unexpected number of values - '
                                     f'{len(values)=} {values=}')

                slot_values = [pattern.replace('#', str(value))
                               for pattern, value in zip(slot_patterns, values)]
                mod = mod_format.format(*slot_values)
                result[mod] = HelmModInfo(
                    display=(variant_index == matched_index),
                    mod=mod,
                    trade_text=trade_text,
                    trade_stat_id=trade_stat_id,
                    trade_stat_value=trade_stat_value
                )

        self._fix_krangled_helm_mods(result)

        return result

    @functools.cached_property
    def mod_trie(self) -> datrie.Trie:
        logger.debug('Creating Trie')
        trie = datrie.Trie(string.printable)
        for mod in self.helm_mods:
            trie[mod] = 1
        return trie

    def get_mod_list_from_ocr_results(self, enchant_list):
        trie = self.mod_trie
        logger.debug(f'Data from OCR{enchant_list}')

        state = datrie.State(trie)
        parts = []
        enchants = []
        for part in enchant_list:
            to_walk = f' {part}' if parts else part
            if state.walk(to_walk):
                parts.append(to_walk)
                continue

            if not parts:
                state.rewind()
                continue

            if parts:
                enchant = ''.join(parts)
                if enchant in trie:
                    enchants.append(enchant)
                elif len(keys := trie.keys(enchant)) == 1 and len(enchant) > 20:
                    enchants.append(keys[0])
                parts = []

            state.rewind()
            if state.walk(part):
                parts.append(part)
                continue

        if parts:
            enchant = ''.join(parts)
            if enchant in trie:
                enchants.append(enchant)
            elif len(keys := trie.keys(enchant)) == 1 and len(enchant) > 20:
                enchants.append(keys[0])

        return enchants

    def _fix_krangled_helm_mods(self, helm_mod_info: Dict[str, HelmModInfo]):
        helm_mod_info['Fireball Always Ignites'].display = False
        helm_mod_info['Fireball has +30% chance to Ignite'].display = True
        helm_mod_info['Burning Arrow Always Ignites'].display = False
        helm_mod_info['Burning Arrow has +30% chance to Ignite'].display = True
