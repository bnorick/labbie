import injector

from labbie.ui.settings.widget import presenter as widget
from labbie.ui.settings.window import view


class SettingsWindowPresenter:

    @injector.inject
    def __init__(self, widget_presenter: widget.SettingsPresenter, view_builder: injector.AssistedBuilder[view.SettingsWindow]):
        self._widget_presenter = widget_presenter
        self._view = view_builder.build(widget=widget_presenter.widget)

        self._view.signal_close.connect(self.close)

    def populate_view(self, results):
        self._widget_presenter.populate_view(results)

    def show(self):
        self._view.show()

    def close(self):
        self._widget_presenter.cleanup()
        self._view.hide()
        self._view.close()

    def add_close_callback(self, callback):
        self._view.signal_close.connect(callback)
