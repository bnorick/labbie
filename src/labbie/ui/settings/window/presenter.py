from sniper.vendor.injector import AssistedBuilder, inject
from sniper.client.ui.flip_assistant.widget.presenter import FlipAssistantPresenter
from .view import FlipAssistantWindow


class FlipAssistantWindowPresenter:
    @inject
    def __init__(self, widget_presenter: FlipAssistantPresenter, view_builder: AssistedBuilder[FlipAssistantWindow]):
        self._widget_presenter = widget_presenter
        self._view = view_builder.build(widget=widget_presenter.widget)

        self._view.signal_close.connect(self.close)

    def show(self):
        self._view.show()

    def populate_view(self, searches, auto_start):
        self._widget_presenter.populate_view(searches, auto_start)

    def close(self):
        self._widget_presenter.cleanup()
        self._view.hide()
        self._view.close()

    def add_close_callback(self, callback):
        self._view.signal_close.connect(callback)
