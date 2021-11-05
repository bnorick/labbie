import injector

from labbie.ui.result.widget import view


class ResultWidgetPresenter:

    @injector.inject
    def __init__(self, view: view.ResultWidget):
        self._view = view

    @property
    def widget(self):
        return self._view

    def populate_view(self, search, league_result, daily_result=None):
        self._view.set_result(search, league_result, daily_result)

    def show(self):
        self._view.show()
