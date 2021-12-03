import injector

from labbie import config
from labbie import constants
from labbie.ui.main.widget import presenter as widget
from labbie.ui.main.window import view

_POSITION_FILE = 'position.txt'


class MainWindowPresenter:

    @injector.inject
    def __init__(self, config_: config.Config, constants_: constants.Constants, widget_presenter: widget.MainPresenter, view_builder: injector.AssistedBuilder[view.MainWindow]):
        self._config = config_
        self._constants = constants_
        self._widget_presenter = widget_presenter
        self._view = view_builder.build(widget=widget_presenter.widget)

        position = None
        if (position_path := self._constants.data_dir / _POSITION_FILE).is_file():
            with position_path.open('r', encoding='utf8') as f:
                position = [int(val) for val in f.read().split()]
        self._view.set_position(position)
        self._view.set_position_path(position_path)

        self._view.signal_close.connect(self.close)
        config_.ui.attach(self, self.on_show_on_taskbar_changed, to='show_on_taskbar')
        self.on_show_on_taskbar_changed(config_.ui.show_on_taskbar)

    def on_show_on_taskbar_changed(self, value: bool):
        self._view.set_taskbar_visibility(value)

    # def reset_position(self):
    #     self._widget_presenter.reset_position()

    def reset_position(self):
        self._view.set_position(None)

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
