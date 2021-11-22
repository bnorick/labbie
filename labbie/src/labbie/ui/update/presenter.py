import asyncio

import injector

from labbie import constants
from labbie import version
from labbie.ui.update import view

_UPDATE_MESSAGE_FORMAT = f'''Current: <strong>v{version.__version__}</strong><br />
Latest {{release_type}}: <strong>v{{version}}</strong>'''
_NO_UPDATE_MESSAGE_FORMAT = f'''Current version (<strong>v{version.__version__}</strong>) is <br />
the latest {{release_type}}.'''


class UpdatePresenter:

    @injector.inject
    def __init__(self, constants_: constants.Constants, view_: view.UpdateMessageBox):
        self._constants = constants_
        self._view = view_

    async def should_update(self, version_: str, release_type: str):
        text = _UPDATE_MESSAGE_FORMAT.format(version=version_, release_type=release_type)


        # When "updating" from prerelease to previous release, we don't show skip
        show_skip = True
        if version.to_tuple(version_) < version.to_tuple(version.__version__):
            show_skip = False

        future = asyncio.Future()
        self._view.ask(text, show_skip, future)
        result = await future
        if result == 'update':
            return True

        if result == 'skip':
            from updater import utils
            utils.set_skipped_version(version_)
        return False

    def no_update_available(self, release_type: str):
        self._view.tell(_NO_UPDATE_MESSAGE_FORMAT.format(release_type=release_type))
