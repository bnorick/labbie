# Labbie
- Hide search window during ocr if it overlays the search area
- Automated packaging / version bumping
- Self update functionality (auto or manual)
- Scrape / Add boot and belt enchants
- Splash screen (waits for resources / enchants to be ready)
- Better 4k support
- Price check for base searches
- Convert enchants to use resource manager
- Selected statistics for results
- Convert resources to a package w/ manager.py, mods.py, trade.py, enchants.py, bases.py
- Make OCR insensitive to c/t using a special character to represent "c or t"
  - This change requires putting the actual enchant strings in the trie as values
- Setting for "Show in task bar"

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
- Automate patch generation (and then signing and upload)


# Packaging
- Run component tests
- If pass, make git tag with `vX.Y.Z` format (or `vX.Y.Z-alpha.P`, `vX.Y.Z-beta.P`, `vX.Y.Z-rc.P` for prereleases) on core version branch
- Push version branch (e.g., `X.Y.Z`) and tag
- Run `python -m package`
- If `release=True`, zip `package/build/Labbie` into `package/build/Labbie_vX_Y_Z.zip`
  - Manually upload to github and make release
- For each component,
  - Move `package/build/Labbie/bin/[COMPONENT_NAME]` to `package/build/historical/[COMPONENT_NAME] X.Y.Z`
  - Run `python -m updater.patch diff SOURCE TARGET` for each source and target needed
  - Add patches to `labbie_admin.updater.utils.repo_dir() / 'targets' / component.name`
- Run `python -m labbie_admin.updater --add-version VERSION --component COMPONENT_NAME`
  - Also verifies version appropriateness
  - Adds patches to update repo
  - Uploads metadata and (new) patches to releases container
  - Updates `releases/components/COMPONENT_NAME/version_history.json`