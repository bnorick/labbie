- Hide search window during ocr if it overlays the search area
- Make OCR a bit more reliable with some image manipulation
- Automated packaging / version bumping
- Self update functionality (auto or manual)
- Scrape / Add boot and belt enchants
- Remember window locations
- Splash screen (waits for resources / enchants to be ready)
- Better 4k support
- Price check for base searches
- Convert enchants to use resource manager
- Selected statistics for results
- Convert resources to a package w/ manager.py, mods.py, trade.py, enchants.py, bases.py


# Major features
## Buy list
- Right click base from enchant window and "Add to buy list"
- Open buy list from labbie main window (pops to the right)
- QListWidget with "Buy" and "Remove" buttons above
- Add right click context menu to base results
    - Add to buy list
## Services
- Add services in the form "mod -- free text note" to an edit box which has line numbers
- OCR'd enchants are marked as "serviceable" in the tab (maybe bg color?)
  - Above the result there would be each matching service note (with the corresponding line number) and a "fulfill" button which removes it from the service list (and maybe adds it to a "completed services" list with timestamp)

## Bugs
- Flame wall OCR reads t as a c, Also the mod has two slots which needs to be handled more gracefully