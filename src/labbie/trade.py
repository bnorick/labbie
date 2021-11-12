import injector
import loguru

from labbie import resources

logger = loguru.logger


@injector.singleton
class Trade:

    @injector.inject
    def __init__(self, resource_manager: resources.ResourceManager):
        self._trade_stats = resource_manager.trade_stats

        self.text_to_stat_id = self._trade_stats
