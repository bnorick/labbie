from typing import Dict, Optional, Tuple

import injector
import loguru

from labbie import resources

logger = loguru.logger


@injector.singleton
class Mods:

    @injector.inject
    def __init__(self, resource_manager: resources.ResourceManager):
        self._resource_manager = resource_manager
        self._mods = resource_manager.mods

        self.helm_mod_to_trade_text = self._build_mod_to_trade_text(self._mods['helm'])

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

