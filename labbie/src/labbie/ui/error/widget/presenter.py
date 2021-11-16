import injector
import loguru

from labbie.ui.error.widget import view

logger = loguru.logger


class ErrorPresenter:

    @injector.inject
    def __init__(self, view: view.ErrorWidget):
        self._view = view

    @property
    def widget(self):
        return self._view

    def cleanup(self):
        pass

    def populate_view(self, exception):
        logger.exception(exception)
        self._view.set_error(str(exception))

    def show(self):
        self._view.show()
