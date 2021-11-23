import asyncio
import injector
import pytest

from os import scandir
from labbie import config
from labbie import constants
from labbie import resources

from labbie.di import module

_Module = module.Module
_Injector = injector.Injector
_Config = config.Config
_Constants = constants.Constants


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
        return loaded


@pytest.fixture(scope='module')
def injector():
    injector = _Injector(_Module())
    resource_manager = injector.get(resources.ResourceManager)

    def initialize_resource_manager_sync(resource_manager):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(resource_manager._get_all_resources())
        finally:
            loop.close()
    initialize_resource_manager_sync(resource_manager)
    return injector
