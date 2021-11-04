import abc
import dataclasses
import pathlib
from typing import Optional

import toml

from labbie import mixins
from labbie import bounds

_Bounds = bounds.Bounds


@dataclasses.dataclass
class BaseConfig(mixins.ObservableMixin, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def load(cls, base_path: pathlib.Path):
        raise NotImplementedError


@dataclasses.dataclass
class HotkeysConfig(mixins.ObservableMixin, mixins.SerializableMixin):
    ocr: Optional[str] = '`'

    @classmethod
    def from_dict(cls, config_dict):
        # handle 'none' in toml to => None
        for field_ in dataclasses.fields(cls):
            key = field_.name
            v = config_dict.get(key, '')
            if type(v) == str and v.lower() == 'none':
                config_dict[key] = None

        return super().from_dict(config_dict)


@dataclasses.dataclass
class OcrConfig(mixins.SerializableMixin):
    bounds: _Bounds = _Bounds(left=335, top=210, right=916, bottom=455)


@dataclasses.dataclass
class UiConfig(mixins.SerializableMixin):
    hotkeys: HotkeysConfig = HotkeysConfig()


@dataclasses.dataclass
class Config(BaseConfig, mixins.SerializableMixin):
    ui: UiConfig = UiConfig()
    ocr: OcrConfig = OcrConfig()
    league: bool = True
    daily: bool = True

    @classmethod
    def from_toml(cls, path: pathlib.Path):
        with path.open() as f:
            config_dict = toml.load(f)
        return cls.from_dict(config_dict)

    @classmethod
    def load(cls, base_path: pathlib.Path):
        path = base_path / 'config.toml'
        return cls.from_toml(path)
