import dataclasses
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
class HelmEnchantInfo:
    enchant: str
    trade_stat_id: Optional[str]
    trade_stat_value: Union[None, int, float]


@injector.singleton
class Mods:

    @injector.inject
    def __init__(self, resource_manager: resources.ResourceManager, trade_: trade.Trade):
        self._resource_manager = resource_manager
        self._trade = trade_

        self._raw_enchants = resource_manager.enchants

        self.helm_enchant_info = self._build_helm_enchant_info(self._raw_enchants['helmet'])  # exact mod -> HelmModInfo

    @functools.cached_property
    def helm_enchants(self):
        return sorted(self.helm_enchant_info.keys())

    def _build_helm_enchant_info(
        self,
        enchants: List[Tuple[str, str, Optional[float]]]
    ) -> Dict[str, HelmEnchantInfo]:
        result = {}
        for enchant, trade_stat_id, trade_stat_value in enchants:
            result[enchant] = HelmEnchantInfo(
                enchant=enchant,
                trade_stat_id=trade_stat_id,
                trade_stat_value=trade_stat_value
            )
        return result

    @functools.cached_property
    def helm_enchant_trie(self) -> datrie.Trie:
        logger.debug('Creating helm enchant trie')
        trie = datrie.Trie(string.printable)
        for mod in self.helm_enchants:
            trie[mod] = 1
        return trie

    def get_enchant_list_from_ocr_results(self, enchant_list):
        trie = self.helm_enchant_trie
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
