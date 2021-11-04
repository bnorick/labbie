from labbie.ui import base
from labbie.ui.search.widget import view as search_widget


class SearchWindow(base.BaseWindow):

    def __init__(self, widget: search_widget.SearchWidget):
        super().__init__(widget=widget)
        self.set_buttons(minimize=True, close=True)
