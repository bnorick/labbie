import dataclasses
import functools
from typing import Dict, Optional, Tuple, Union

import injector
import loguru

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

        print(self._raw_mods)
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
