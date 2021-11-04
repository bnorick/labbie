import dataclasses
from typing import List, Optional

from labbie import enchants


@dataclasses.dataclass
class Result:
    title: str
    search: str
    league_result: Optional[List[enchants.Enchant]]
    daily_result: Optional[List[enchants.Enchant]]
