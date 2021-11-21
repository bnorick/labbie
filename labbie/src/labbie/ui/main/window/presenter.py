import injector

from labbie import config
from labbie.ui.main.widget import presenter as widget
from labbie.ui.main.window import view


class MainWindowPresenter:

    @injector.inject
    def __init__(self, config_: config.Config, widget_presenter: widget.MainPresenter, view_builder: injector.AssistedBuilder[view.MainWindow]):
        self._config = config_
        self._widget_presenter = widget_presenter
        self._view = view_builder.build(widget=widget_presenter.widget)

        self._view.signal_close.connect(self.close)
        config_.ui.attach(self, self.on_show_on_taskbar_changed, to='show_on_taskbar')
        self.on_show_on_taskbar_changed(config_.ui.show_on_taskbar)

    def on_show_on_taskbar_changed(self, value: bool):
        self._view.set_taskbar_visibility(value)

    def reset_position(self):
        self._widget_presenter.reset_position()

    def populate_view(self, results, clear):
        self._widget_presenter.populate_view(results, clear)

    def show(self):
        self._view.show()

    def toggle(self):
        self._view.toggle()

    def close(self):
        self._widget_presenter.cleanup()
        self._view.hide()
        self._view.close()

    def add_close_callback(self, callback):
        self._view.signal_close.connect(callback)
