import enum


class Sentinel(enum.Enum):
    NOT_LOADED = enum.auto()
    NOT_SET = enum.auto()
    NOT_CONFIGURED = enum.auto()
    DEFAULT = enum.auto()
