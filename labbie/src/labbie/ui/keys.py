import abc
import asyncio
import dataclasses
import inspect
from typing import ClassVar, List, Union

import injector

from labbie import result
from labbie.ui.about.window import presenter as about
from labbie.ui.system_tray import presenter as system_tray
from labbie.ui.search.window import presenter as search
from labbie.ui.settings.window import presenter as settings
from labbie.ui.error.window import presenter as error


@dataclasses.dataclass(frozen=True)
class _Key(abc.ABC):
    DELETE_WHEN_CLOSED: ClassVar[bool] = False

    @abc.abstractmethod
    def get_presenter(self, injector: injector.Injector):
        raise NotImplementedError

    def show(self, presenter):
        presenter.show()

    def toggle(self, presenter):
        presenter.toggle()


@dataclasses.dataclass(frozen=True)
class _PopulatableKey(_Key):
    @abc.abstractmethod
    def _populate_presenter(self, presenter):
        raise NotImplementedError

    def show(self, presenter):
        populate_result = self._populate_presenter(presenter)
        if inspect.iscoroutine(populate_result):
            asyncio.create_task(self._show_after_populate(presenter, populate_result))
        else:
            presenter.show()

    async def _show_after_populate(self, presenter, populate_task):
        await populate_task
        presenter.show()


@dataclasses.dataclass(frozen=True)
class SystemTrayIconKey(_Key):
    def get_presenter(self, injector: injector.Injector):
        return injector.get(system_tray.SystemTrayIconPresenter)


@dataclasses.dataclass(frozen=True)
class SearchWindowKey(_PopulatableKey):
    DELETE_WHEN_CLOSED: ClassVar[bool] = False
    results: Union[None, result.Result, List[result.Result]] = dataclasses.field(default=None, compare=False)
    clear: bool = dataclasses.field(default=False, compare=False)

    def get_presenter(self, injector: injector.Injector):
        return injector.get(search.SearchWindowPresenter)

    def _populate_presenter(self, presenter: search.SearchWindowPresenter):
        presenter.populate_view(self.results, clear=self.clear)


@dataclasses.dataclass(frozen=True)
class ErrorWindowKey(_PopulatableKey):
    DELETE_WHEN_CLOSED: ClassVar[bool] = True
    exception: Exception = dataclasses.field(compare=False)

    def get_presenter(self, injector: injector.Injector):
        return injector.get(error.ErrorWindowPresenter)

    def _populate_presenter(self, presenter: error.ErrorWindowPresenter):
        presenter.populate_view(self.exception)


@dataclasses.dataclass(frozen=True)
class SettingsWindowKey(_Key):
    DELETE_WHEN_CLOSED: ClassVar[bool] = True

    def get_presenter(self, injector: injector.Injector):
        return injector.get(settings.SettingsWindowPresenter)


@dataclasses.dataclass(frozen=True)
class AboutWindowKey(_Key):
    DELETE_WHEN_CLOSED: ClassVar[bool] = True

    def get_presenter(self, injector: injector.Injector):
        return injector.get(about.AboutWindowPresenter)
