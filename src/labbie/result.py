import dataclasses
from typing import List, Optional

from labbie import enchants


@dataclasses.dataclass
class Result:
    title: str
    search: str
    league_result: Optional[List[enchants.Enchant]]
    daily_result: Optional[List[enchants.Enchant]]

    def __repr__(self):
        if self.league_result:
            league_result_repr = [self.league_result[0]]
            if len(self.league_result) > 1:
                league_result_repr.append(f'(... {len(self.league_result) - 1} other results ...)')
        else:
            league_result_repr = self.league_result

        if self.daily_result:
            daily_result_repr = [self.daily_result[0]]
            if len(self.daily_result) > 1:
                daily_result_repr.append(f'(... {len(self.daily_result) - 1} other results ...)')
        else:
            daily_result_repr = self.daily_result

        return f'{type(self).__name__}(title={self.title!r}, search={self.search!r}, league_result={daily_result_repr!r}, daily_result={daily_result_repr!r})'