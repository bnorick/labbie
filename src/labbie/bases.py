import dataclasses
import functools

import injector

from labbie import resources
from labbie import utils


@dataclasses.dataclass
class _Helm:
    display_text: str
    base: str
    unique: bool
Helm = utils.make_slotted_dataclass(_Helm)  # noqa: E305


@injector.singleton
class Bases:

    @injector.inject
    def __init__(self, resource_manager: resources.ResourceManager):
        self._items = resource_manager.items

        self.helms = self._build_helms()

    @functools.cached_property
    def helm_display_texts(self):
        return sorted(helm.display_text for helm in self.helms.values())

    def _build_helms(self):
        helms = {}
        for unique, display_text, base in self._items['helmet']:
            helms[display_text] = Helm(display_text=display_text, base=base, unique=unique)
        return helms
