import dataclasses
import enum
from typing import Optional

import injector

from labbie import enchants
from labbie import mixins


class State(enum.Enum):
    STARTING = 'Starting'
    OCR = 'Scanning enchants'
    READY = 'Ready'
    ERROR = 'Error'


@injector.singleton
@dataclasses.dataclass
class AppState(mixins.ObservableMixin):
    state: State = State.STARTING
    league_enchants: enchants.Enchants = enchants.Enchants('league')
    daily_enchants: enchants.Enchants = enchants.Enchants('daily')
    last_error: Optional[str] = None

    def __setattr__(self, name, val):
        cls_fields = {f.name for f in dataclasses.fields(self)}
        if name not in cls_fields:
            object.__setattr__(self, name, val)
            return

        cur_val = getattr(self, name)
        if cur_val != val:
            object.__setattr__(self, name, val)
            self.notify(**{name: val})
