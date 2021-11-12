import dataclasses
import functools
import os
import pathlib
from typing import ClassVar, Union

import dacite
import loguru
import toml

from labbie import mixins, version
from labbie import utils

logger = loguru.logger
_DEFAULT_DATA_DIR = utils.default_data_dir()
_DEFAULT_CONFIG_DIR = utils.default_config_dir()
_MISSING = object()


@dataclasses.dataclass(frozen=True)
class BaseConstants(mixins.SerializableMixin):
    @classmethod
    def load(cls, _constants_path: Union[None, str, pathlib.Path] = _MISSING, **kwargs):
        """Load constants.

        There are three potential sources for constant values, in order of their preference
        (from highest to lowest):
            1) Environment variables with names matching "LABBIE_[CONSTANT_ENV_VAR_NAME]", e.g.,
            LABBIE_DATA_DIR corresponds with the data_dir constant.
            2) Keyword arguments.
            3) Constants toml file.
        """
        if _constants_path is not _MISSING:
            path_source = 'kwarg'
            if _constants_path:
                _constants_path = pathlib.Path(_constants_path)
        else:
            path_source = 'default'
            _constants_path = cls._DEFAULT_PATH

        valid_names = {field.name for field in dataclasses.fields(cls)}

        explicit_vals = {}
        for name, val in kwargs.items():
            if name in valid_names:
                logger.info(f'Overriding constant "{name}" from kwarg, {val=}.')
                explicit_vals[name] = val
            else:
                raise ValueError(f'Invalid kwarg "{name}", no such field.')

        env_prefix = 'labbie_'
        if extra_prefix := getattr(cls, '_ENV_PREFIX', None):
            env_prefix += f'{extra_prefix.lower()}_'
        for name, val in os.environ.items():
            if name.lower().startswith(env_prefix):
                field_name = name.lower()[len(env_prefix):]  # remove the prefix
                if field_name in valid_names:
                    logger.info(f'Overriding constant "{cls.__name__}.{field_name}" from environment variable ({name}), {val=}.')
                    explicit_vals[field_name] = val
                elif field_name == 'constants':
                    path_source = 'env var'
                    _constants_path = pathlib.Path(val)

        if _constants_path:
            # when constants path is explicitly set, the corresponding file must exist
            if _constants_path.is_file():
                logger.info(f'Loading constants from {_constants_path} specified by {path_source} (with {len(explicit_vals)} overrides).')
                constants = cls.from_toml(_constants_path, overrides=explicit_vals)
            elif path_source != 'default':
                    raise ValueError(f'The path provided to load {cls.__name__} is not a file: {_constants_path}')
            else:
                logger.info('Loading constants from environment variables and kwargs.')
                constants = cls.from_dict(explicit_vals)
        else:
            logger.info('Loading constants from environment variables and kwargs.')
            constants = cls.from_dict(explicit_vals)

        logger.debug(f'{constants=}')

        return constants

    @classmethod
    def from_toml(cls, path: pathlib.Path, overrides=None):
        with path.open() as f:
            d = toml.load(f)
        if overrides:
            d.update(overrides)
        return cls.from_dict(d)

    @classmethod
    def from_dict(cls, d):
        config = dacite.Config(
            cast=[pathlib.Path],
            type_hooks={bool: lambda v: v if isinstance(v, bool) else v.lower() in ('t', 'true', '1')}
        )
        return super().from_dict(d, config=config)


@dataclasses.dataclass(frozen=True)
class Constants(BaseConstants):
    _DEFAULT_PATH: ClassVar[pathlib.Path] = utils.default_config_dir() / 'constants.toml'

    debug: bool = False
    data_dir: pathlib.Path = _DEFAULT_DATA_DIR
    config_dir: pathlib.Path = _DEFAULT_CONFIG_DIR
    user_agent: str = f'Labbie v{version.__version__}'
    dilate: bool = False

    @functools.cached_property
    def logs_dir(self):
        return utils.logs_dir()

    @functools.cached_property
    def helm_enchants_dir(self):
        return self.data_dir / 'helm'

    @functools.cached_property
    def screenshots_dir(self):
        return self.data_dir / 'screenshots'

    @functools.cached_property
    def resources_dir(self):
        return self.data_dir / 'resources'

    @classmethod
    def from_toml(cls, path: pathlib.Path, overrides=None):
        with path.open() as f:
            d = toml.load(f)
        if overrides:
            d.update(overrides)
        return cls.from_dict(d)
