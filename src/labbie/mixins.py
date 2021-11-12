import collections
import copy
import dataclasses
import enum
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Set, Union

import dacite
import loguru

logger = loguru.logger


class Sentinel(enum.Enum):
    NOT_LOADED = enum.auto()
    NOT_SET = enum.auto()
    NOT_CONFIGURED = enum.auto()
    DEFAULT = enum.auto()


@dataclasses.dataclass
class ObserverHandlers:
    generic_handler: Optional[Callable] = None
    event_handlers: Dict[str, Callable] = dataclasses.field(default_factory=dict)

    def __hash__(self):
        return id(self)


class ObservableMixin:
    def __init__(self):
        self._observer_handlers: Dict[Any, ObserverHandlers] = {}
        self._generic_observer_handlers: Set[ObserverHandlers] = set()
        self._event_observer_handlers: Dict[str, Set[ObserverHandlers]] = collections.defaultdict(set)

    def __post_init__(self):
        if dataclasses.is_dataclass(self):
            try:
                super().__post_init__()
            except AttributeError:
                pass
            self._observer_handlers = {}
            self._generic_observer_handlers = set()
            self._event_observer_handlers = collections.defaultdict(set)

    def attach(self, observer, handler, to: Union[str, Sequence[str]] = None):
        """Attaches a handler and an observer to this observable.

        The provided handler is either attached generically (when `to` is not provided)
        or to a specific event or set of events.
        """
        handlers = self._observer_handlers.setdefault(observer, ObserverHandlers())
        if to is None:
            if handlers.generic_handler is not None:
                logger.warning(f'Overriding generic handler for {observer} observing {self}.')
            handlers.generic_handler = handler
            self._generic_observer_handlers.add(handlers)
        else:
            events = (to, ) if isinstance(to, str) else to
            for event in events:
                if event in handlers.event_handlers:
                    logger.warning(f'Overriding "{event}" event handler for {observer} observing {self}.')
                handlers.event_handlers[event] = handler
                self._event_observer_handlers[event].add(handlers)

    def detatch(self, observer, generic: bool = None, events: Iterable[str] = None):
        observer_handlers = self._observer_handlers.get(observer)
        if observer_handlers:
            if generic is None and events is None:
                # fully detach
                del self._observer_handlers[observer]
                self._generic_observer_handlers.discard(observer_handlers)
                for event in observer_handlers.event_handlers:
                    self._event_observer_handlers[event].discard(observer_handlers)
            else:
                if generic:
                    observer_handlers.generic_handler = None
                    self._generic_observer_handlers.discard(observer_handlers)

                if events:
                    for event in events:
                        self._event_observer_handlers[event].discard(observer_handlers)
                        observer_handlers.event_handlers.pop(event, None)

    def notify(self, _log=True, **kwargs):
        if kwargs:
            for event, args in kwargs.items():
                if not isinstance(args, tuple):
                    args = (args, )
                if _log:
                    logger.debug(f'{self.__class__.__module__}.{self.__class__.__name__} notify, {event=} {args=}')
                for handler in self._event_observer_handlers[event]:
                    handler.event_handlers[event](*args)
        if _log:
            logger.debug(f'{self.__class__.__module__}.{self.__class__.__name__} generic notify')
        # generic notify to call generic handler
        for handler in self._generic_observer_handlers:
            handler.generic_handler(self)


_SERIALIZABLE_CLASSES = {}
_TYPE_HOOKS = {}
_DEFAULT_DACITE_CONFIG = dacite.Config(type_hooks=_TYPE_HOOKS)


def _make_type_hook(cls):
    def type_hook(value):
        logger.debug(f'HOOKED {cls.__module__}.{cls.__name__}')
        if isinstance(value, cls):
            return value
        elif isinstance(value, dict):
            return cls.from_dict(value)
        raise ValueError(f'Can\'t convert {value=} to type {cls.__module__}.{cls.__name__}')
    return type_hook


def _register_serializable_class(cls):
    key = f'{cls.__module__}.{cls.__name__}'
    if key not in _SERIALIZABLE_CLASSES:
        _SERIALIZABLE_CLASSES[key] = cls
        _TYPE_HOOKS[cls] = _make_type_hook(cls)


class SerializableMixin:
    def __init_subclass__(cls, **kwargs):
        _register_serializable_class(cls)
        super().__init_subclass__(**kwargs)

    @staticmethod
    def _dict_factory(result):
        # NOT_LOADED should only be a default value, so we're
        # safe to just remove it
        d = {}
        for k, v in result:
            if k.startswith('_') or v is Sentinel.NOT_LOADED:
                continue
            d[k] = v
        return d

    def as_dict(self):
        d = dataclasses.asdict(self, dict_factory=self._dict_factory)
        if version := self.migration_version():
            d['__VERSION__'] = version
        return d

    @classmethod
    def migration_version(cls):
        v = {}
        classes = cls.__mro__

        # NOTE (bnorick): it's ok to override cls here because we don't need
        # it any longer
        for cls in classes:
            if '_VERSION' in cls.__dict__:
                v[f'{cls.__module__}.{cls.__name__}'] = cls._VERSION
        return v or None

    @classmethod
    def versioned_classes(cls):
        versioned_classes = {}
        for c in cls.__mro__:
            if '_VERSION' in c.__dict__:
                versioned_classes[f'{c.__module__}.{c.__name__}'] = c
        return versioned_classes

    @classmethod
    def migrate(cls, d):
        d_migration_version = d.pop('__VERSION__', None)
        if not d_migration_version:
            return d

        # NOTE (bnorick): I don't think the following logic for combining multiple migrations
        # is not resilient to inheritance changes, if we ever need to do that we'll have to adjust
        # this logic.

        versioned_classes = cls.versioned_classes()
        cur_migration_version = cls.migration_version()

        class_migrated_d = {}
        for class_name, to_v in cur_migration_version.items():
            from_v = d_migration_version[class_name]
            class_migrated = copy.deepcopy(d)
            for v1 in range(from_v, to_v):
                v2 = v1 + 1
                versioned_classes[class_name]._incremental_migration(class_migrated, v1, v2)
            class_migrated_d[class_name] = class_migrated

        # the most specific classes should be combined last, thereby overriding
        # more generic migrations with more specific
        class_order = reversed(versioned_classes.keys())
        migrated_d = class_migrated_d[next(class_order)]
        for class_name in class_order:
            migrated_d.update(class_migrated_d[class_name])

        return migrated_d

    @classmethod
    def _incremental_migration(cls, d, v1, v2):
        migrations = cls.__dict__['_MIGRATIONS']
        migration_fn = getattr(migrations, f'v{v1}_to_v{v2}', None)
        if not migration_fn:
            raise RuntimeError(f'Missing migration from v{v1} to v{v2}.')

        return migration_fn(d)

    @classmethod
    def from_dict(cls, d, **kwargs):
        logger.debug(f'{cls.__module__}.{cls.__name__} __VERSION__={d.get("__VERSION__", "Missing")}')

        d = cls.migrate(d)
        try:
            if config := kwargs.get('config'):
                type_hooks = _TYPE_HOOKS.copy()
                type_hooks.update(config.type_hooks)
                config = copy.deepcopy(config)
                config.type_hooks = type_hooks
                kwargs['config'] = config
            else:
                kwargs['config'] = _DEFAULT_DACITE_CONFIG
            return dacite.from_dict(data_class=cls, data=d, **kwargs)
        except:
            import pprint
            logger.debug(cls)
            logger.debug(pprint.pformat(d))
            raise
