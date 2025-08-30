# V23 Migration Guide — Modern-only Transition

This guide helps you migrate code, tests, and workflows to V23 where Modern is the only UI. Legacy/v7 switching is removed.

## What Changed
- Removed GUI version switching (Legacy/v7). Modern is the only interface.
- Presenter context/schema no longer includes `gui_version`.
- View does not expose a GUI version selector; the UI initializes as Modern.
- Tree vs Flat visual behavior is explicit:
  - Tree uses `show="tree headings"` with hierarchical expand/collapse.
  - Flat uses `show="headings"` and shows no children.
- Flat display nodes from Model have `children=[]`.

## Action Items

### 1) Update Imports/Exports
- Remove imports/usages of `StructViewV7` and `V7Presenter`.
- Use `from src.view import StructView` and `from src.presenter import StructPresenter` only.

### 2) Update Presenter Context Usage
- Remove any code/tests relying on `context["gui_version"]`.
- Validate context using `src/presenter/context_schema.PRESENTER_CONTEXT_SCHEMA` (no gui_version).

### 3) Update View Logic & Tests
- Remove GUI version selector test steps and `view._on_gui_version_change(...)` calls.
- Verify Modern initializes by default; interact with `view.member_tree` (or `view.modern_tree` if present).
- Add assertions for Tree/Flat:
  - Tree: `member_tree.cget("show")` includes `"tree"`, nested children exist.
  - Flat: `member_tree.cget("show") == "headings"`, no nested children.

### 4) Update UI Strings
- Remove `label_gui_version` and any references.

### 5) Remove v7 Artifacts
- Delete or ignore `src/view/struct_view_v7.py`, `src/presenter/v7_presenter.py`, and related tests.
- Ensure `src/view/__init__.py` and `src/presenter/__init__.py` do not export v7 classes.

### 6) CI/Build Scripts
- Remove steps that run v7 tests or depend on gui_version switching.

## Backward Compatibility Notes
- Any scripts or automations relying on v7/legacy switching must be updated to Modern-only. Most code should continue to work if it did not explicitly depend on gui_version or v7 classes.

## Verification Checklist
- [ ] No references to `gui_version` in code or tests
- [ ] No references to `StructViewV7` or `V7Presenter`
- [ ] Tree/Flat tests pass (visual behavior)
- [ ] UI keys test passes after removing `label_gui_version`
- [ ] CHANGELOG includes V23 notes

## Links
- CHANGELOG: `/CHANGELOG.md`
- View README (V23): `src/view/README.md`
- V23 Planning Document: `docs/development/v23_Modern_Replaces_Legacy_and_TreeFlat_Visual_Diff_TDD.md`