import injector

from labbie.ui.search.widget import presenter as widget
from labbie.ui.search.window import view


class SearchWindowPresenter:

    @injector.inject
    def __init__(self, widget_presenter: widget.SearchPresenter, view_builder: injector.AssistedBuilder[view.SearchWindow]):
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
