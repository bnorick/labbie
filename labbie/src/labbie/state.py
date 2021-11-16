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
    resources_ready: bool = False
    league_enchants: enchants.Enchants = enchants.Enchants('league')
    daily_enchants: enchants.Enchants = enchants.Enchants('daily')
    last_error: Optional[str] = None

    def ensure_scrape_enabled(self):
        league_disabled = self.league_enchants.state is enchants.State.DISABLED
        daily_disabled = self.daily_enchants.state is enchants.State.DISABLED
        if league_disabled and daily_disabled:
            raise RuntimeError('No enchant scrapes are enabled, please edit the settings.')

    def __setattr__(self, name, val):
        cls_fields = {f.name for f in dataclasses.fields(self)}
        if name not in cls_fields:
            object.__setattr__(self, name, val)
            return

        cur_val = getattr(self, name)
        if cur_val != val:
            object.__setattr__(self, name, val)
            self.notify(**{name: val})
