import os
import pathlib

from labbie import utils as labbie_utils
from updater import utils

with labbie_utils.temporary_freeze():
    from labbie import constants

# Use explicit paths here because we're actually loading labbie from the build
# directory (as that's what is updatable) but sys.frozen may or may not be set
os.environ['LABBIE_DATA_DIR'] = str(utils.root_dir() / 'data')
os.environ['LABBIE_CONFIG_DIR'] = str(utils.root_dir() / 'config')
LABBIE_CONSTANTS = constants.Constants.load(
    _constants_path=pathlib.Path(utils.root_dir() / 'config' / 'constants.toml'))
