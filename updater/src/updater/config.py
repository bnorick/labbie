from labbie import config
from updater import constants

LABBIE_CONFIG = config.Config.load(base_path=constants.LABBIE_CONSTANTS.config_dir)
