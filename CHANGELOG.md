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

### API Changes (Examples)
- Removed: `StructPresenter.on_switch_gui_version(version)`
  - Before:
    ```python
    presenter.on_switch_gui_version("modern")
    ```
  - After: No-op. Modern is default. Remove such calls.

- Removed: GUI version selector in `StructView`
  - Before: `view.gui_version_var`, `view.gui_version_menu`, `view._on_gui_version_change("modern")`
  - After: Not available. Modern initializes by default.

- Display mode remains:
  ```python
  view._on_display_mode_change("tree")  # Tree: show="tree headings"
  view._on_display_mode_change("flat")  # Flat: show="headings"
  ```

- Model flat nodes have no children:
  ```python
  nodes = model.get_display_nodes("flat")
  assert all(not n.get("children") for n in nodes)
  ```

## Earlier versions
- See docs/development for historical design notes and version plans.