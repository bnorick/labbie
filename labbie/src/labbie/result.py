import dataclasses
from typing import List, Optional

from labbie import enchants


@dataclasses.dataclass
class Result:
    title: str
    search: str
    base: bool  # is this a result from a base search
    league_result: Optional[List[enchants.Enchant]]
    daily_result: Optional[List[enchants.Enchant]]

    def _summary(self, type_: str, base: bool):
        results = getattr(self, f'{type_}_result')
        if results is None:
            return None
        if base:
            return f'{type_.upper()} ({len(results)})\n{enchants.base_summary(results)}'
        return f'{type_.upper()} ({len(results)})\n{enchants.enchant_summary(results)}'

    def league_summary(self, base):
        return self._summary('league', base)

    def daily_summary(self, base):
        return self._summary('daily', base)

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