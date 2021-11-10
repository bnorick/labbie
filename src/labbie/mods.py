import string
import functools
from typing import Dict, Optional, Tuple

import injector
import loguru
import datrie

from labbie import resources

logger = loguru.logger


@injector.singleton
class Mods:

    @injector.inject
    def __init__(self, resource_manager: resources.ResourceManager):
        self._resource_manager = resource_manager
        self._mods = resource_manager.mods

        self.helm_mod_to_trade_text = self._build_mod_to_trade_text(self._mods['helmet'])

    @functools.cached_property
    def mod_trie(self) -> datrie.Trie:
        trie = datrie.Trie(string.printable)
        for type, mods in self._mods.items():
            for mod, formats in mods.items():
                trie[mod] = formats
        return trie

    def get_mod_list_from_ocr_results(self, enchant_list):
        trie = self.mod_trie

        full_enchants = []
        potential_enchants = []
        for partial_enchant in enchant_list:
            if partial_enchant == '':
                continue
            partial_enchant = partial_enchant.lower().replace('’', "'")
            # continuation of enchant
            if potential_enchants:
                is_partial_enchant = False
                for enchant in potential_enchants:
                    if partial_enchant in enchant:
                        logger.debug(f'partial part of previous {partial_enchant=}')
                        if enchant not in full_enchants:
                            full_enchants.append(enchant)
                        is_partial_enchant = True
                if is_partial_enchant:
                    continue
                # odd scenario where there are multiple potential enchants but no follow up lines
                # to determine wich is correct main scenario this happens is with plurals
                if len(potential_enchants) > 1:
                    full_enchants.extend(potential_enchants)
            potential_enchants = trie.keys(partial_enchant)

            if len(potential_enchants) == 1:
                full_enchants.append(potential_enchants[0])
        if len(potential_enchants) > 1:
            full_enchants.extend(potential_enchants)
        logger.info(f'found {full_enchants=}')
        return full_enchants
        for enchant
        trie.prefixes

    def _build_mod_to_trade_text(self, mods: Dict[str, Tuple[str, Optional[int]]]):
        result = {}
        for mod_format, (slot_entry, value) in mods.items():
            if '{' not in mod_format:
                result[mod_format] = mod_format
                continue

            slotted = mod_format.format(slot_entry)
            if slotted in self._resource_manager.trade:
                trade_text = slotted
            elif (hash_only_slotted := mod_format.format('#')) in self._resource_manager.trade:
                trade_text = hash_only_slotted
            else:
                logger.debug(f'Unable to find trade text for {mod_format=}')
                continue

            mod = slotted.replace('#', value)
            result[mod] = trade_text
        return result

