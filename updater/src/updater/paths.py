import dataclasses
import pathlib
import shutil
import sys
from typing import Optional


@dataclasses.dataclass
class Paths:
    root: pathlib.Path
    data: Optional[pathlib.Path]
    updater_data: pathlib.Path = dataclasses.field(init=False)
    repo: pathlib.Path = dataclasses.field(init=False)
    downloads: pathlib.Path = dataclasses.field(init=False)
    work: pathlib.Path = dataclasses.field(init=False)

    def __post_init__(self):
        if self.data is None:
            self.data = self.root / 'data'
        self.updater_data = self.data / 'updater'
        self.repo = self.updater_data / 'repo'
        self.downloads = self.updater_data / 'downloads'
        self.work = self.updater_data / 'work'

        if not self.repo.exists():
            # paths which depend on frozen state
            if getattr(sys, '_really_frozen', False):
                repo_source = self.root / 'bin' / 'updater' / 'repo'
            else:
                repo_source = self.root / 'updater' / 'repo'
            shutil.copytree(repo_source, self.repo)
