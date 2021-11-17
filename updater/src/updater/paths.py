import dataclasses
import pathlib
import sys
from typing import Optional


@dataclasses.dataclass
class Paths:
    root: pathlib.Path
    data: Optional[pathlib.Path]
    updater_data: pathlib.Path = dataclasses.field(init=False)
    downloads: pathlib.Path = dataclasses.field(init=False)
    work: pathlib.Path = dataclasses.field(init=False)
    updater_repo: pathlib.Path = dataclasses.field(init=False)

    def __post_init__(self):
        if self.data is None:
            self.data = self.root / 'data'
        self.updater_data = self.data / 'updater'
        self.downloads = self.updater_data / 'downloads'
        self.work = self.updater_data / 'work'

        # paths which depend on frozen state
        if getattr(sys, 'frozen', False):
            self.updater_repo =  self.root / 'bin' / 'updater' / 'repo'
        else:
            self.updater_repo =  self.root / 'updater' / 'repo'
