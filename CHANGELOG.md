# Changelog

## V23 (Modern-only, Tree/Flat visual distinction)
- Removed Legacy and v7 GUI version switching. Modern is now the only UI.
- Presenter context/schema no longer includes `gui_version`.
- View no longer exposes GUI version selector; initialization defaults to Modern.
- Tree vs Flat visual behavior:
  - Tree uses `show="tree headings"`, supports hierarchical expand/collapse.
  - Flat uses `show="headings"`, displays a flat list without children.
- Model `get_display_nodes("flat")` now strips children for each node.
- Tests updated accordingly; added dedicated Tree/Flat visual tests.
- Deprecated/removed code:
  - Removed `StructViewV7` and `V7Presenter` from public exports. v7 files and tests removed.
  - Removed `label_gui_version` UI string key.

## Earlier versions
- See docs/development for historical design notes and version plans.