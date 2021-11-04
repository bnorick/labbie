import injector

from labbie.ui.result.widget import view


class ResultWidgetPresenter:

    @injector.inject
    def __init__(self, view: view.ResultWidget):
        self._view = view

    @property
    def widget(self):
        return self._view

    def populate_view(self, search, result):
        self._view.set_result(search, result)

    def show(self):
        self._view.show()
