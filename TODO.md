- Hide search window during ocr if it overlays the search area
- Make OCR a bit more reliable with some image manipulation
- Add enchant verification to OCR
  - requires full enchant list from repoe
  - github api to detect changes to repoe content (via commit id for )
- Automated packaging / version bumping
- Self update functionality (auto or manual)
- Scrape / Add boot and belt enchants
- Remember window locations
- Add ratelimited error handling to the buy urls
- Color for selected league / daily text with toggle
- Splash screen (waits for resources / enchants to be ready)
- Move enchants downloading to resource manager (?)
- 4k

# Major features
## Price checking
- [X] Modify top row of results
  - [X] Switch becomes a toggle, league and daily show counts
- Add a pane to the right of results
  - Price check button
    - Unclickable if there is no selection
  - [X] Copy button
  - Selected statistics which update on selection change
    - Percent and number/total for all selected
    - Percent and number/base total for each base partially selected
- List for results
  - [X] Sub results are indented a bit
  - Selected set of ilvls for base will converted into minimal number of searches
  - Multiple bases can be selected
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