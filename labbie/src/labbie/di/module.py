import injector
import loguru

from labbie import config
from labbie import constants

logger = loguru.logger


class Module(injector.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.constants_kwargs = kwargs

    @injector.singleton
    @injector.provider
    def provide_constants(self) -> constants.Constants:
        return constants.Constants.load(**self.constants_kwargs)

    @injector.singleton
    @injector.provider
    def provide_config(self, constants: constants.Constants) -> config.Config:
        loaded = config.Config.load(base_path=constants.config_dir)
        logger.debug(f'Loaded config {loaded}')
        return loaded
