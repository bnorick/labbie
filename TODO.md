# Labbie
- Hide search window during ocr if it overlays the search area
- [X] Automated packaging / version bumping
- [X] Self update functionality (auto or manual)
- Scrape / Add boot and belt enchants
- Splash screen (waits for resources / enchants to be ready)
- Better 4k support
- Price check for base searches
- Convert enchants to use resource manager
- Selected statistics for results
- Convert resources to a package w/ manager.py, mods.py, trade.py, enchants.py, bases.py
- Make OCR insensitive to c/t using a special character to represent "c or t"
  - This change requires putting the actual enchant strings in the trie as values
- [X] Setting for "Show in task bar"
- Make buttons for "Reset Window Positions" and "Check for Updates" not full width
- Make `Config` versioned so that prerelease rollbacks can also rollback config

## Major features
### Buy list
- Right click base from enchant window and "Add to buy list"
- Open buy list from labbie main window (pops to the right)
- QListWidget with "Buy" and "Remove" buttons above
- Add right click context menu to base results
    - Add to buy list
### Services
- Add services in the form "mod -- free text note" to an edit box which has line numbers
- OCR'd enchants are marked as "serviceable" in the tab (maybe bg color?)
  - Above the result there would be each matching service note (with the corresponding line number) and a "fulfill" button which removes it from the service list (and maybe adds it to a "completed services" list with timestamp)


# Updater
- Rewrite esky code, it's... dated.
- [X] Automate patch generation (and then signing and upload)


# Packaging
- Better automation
  - Run component tests
  - If pass, make git tag with `{component_name}/X.Y.Z` format (or `X.Y.Z-alpha.P`, `X.Y.Z-beta.P`, `X.Y.Z-rc.P` for prereleases) on core version branch
  - Push version branch (e.g., `X.Y.Z`) and tag
  - Run `package.build`
  - Run `package.deploy`
- Add some way to un-release, maybe?

# Generalize Updater and Packager
In order to extract the updater and packages and make them more generalized for use in other projects, we need to
- Support component specification in pyproject.toml under \[tools.skif] or skif.toml (so one doesn't have to distribute pyproject.toml)
- Remove component spec from updater and dependency on it in packager
- Separate out GUI from updater
- Support azure blob or github for packager
- Bring TUF components from labbie_admin into packager