import pathlib

from labbie import constants
from updater import utils

# Use an explicit path here because we're actually loading labbie from the built (i.e., frozen)
# version of labbie directory (as that's what is updatable) but sys.frozen may or may not be set
CONSTANTS = constants.Constants.load(
    _constants_path=pathlib.Path(utils.root_dir() / 'config' / 'constants.toml'))
