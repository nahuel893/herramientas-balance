# Storage Specification

## Purpose

Local persistence layer for named selections. Responsible for reading and writing `selections.json`. Extracted from the helpers currently embedded in `app/main.py`. MUST NOT contain HTTP logic.

## Requirements

### Requirement: load_selections

The module MUST expose `load_selections() -> dict` that reads `selections.json` and returns its contents as a dict.

#### Scenario: File exists with data

- GIVEN `selections.json` exists and contains a valid JSON object
- WHEN `load_selections()` is called
- THEN it returns the parsed dict

#### Scenario: File does not exist

- GIVEN `selections.json` does not exist on disk
- WHEN `load_selections()` is called
- THEN it returns an empty dict `{}`

---

### Requirement: save_selection

The module MUST expose `save_selection(name: str, table: str, columns: list[str]) -> None` that persists a new or updated selection to `selections.json`.

Each selection entry MUST contain keys: `table` (str), `columns` (list[str]), `created_at` (ISO 8601 datetime string).

Saving a selection with the same `name` as an existing one MUST overwrite it.

#### Scenario: Save new selection

- GIVEN `selections.json` exists with zero or more entries
- WHEN `save_selection("mi_reporte", "ventas", ["id", "monto"])` is called
- THEN `selections.json` contains a new entry `"mi_reporte"` with the provided table, columns, and a `created_at` timestamp
- AND previously existing entries are unchanged

#### Scenario: Overwrite existing selection

- GIVEN a selection named `"mi_reporte"` already exists
- WHEN `save_selection("mi_reporte", "ventas", ["id"])` is called
- THEN the entry is overwritten with the new values

#### Scenario: File does not exist yet

- GIVEN `selections.json` does not exist
- WHEN `save_selection(...)` is called
- THEN `selections.json` is created with the new entry

---

### Requirement: delete_selection

The module MUST expose `delete_selection(name: str) -> bool` that removes a selection by name from `selections.json`. It MUST return `True` if the entry was found and deleted, `False` if it was not found.

#### Scenario: Delete existing selection

- GIVEN a selection named `"mi_reporte"` exists in `selections.json`
- WHEN `delete_selection("mi_reporte")` is called
- THEN the entry is removed from `selections.json`
- AND the function returns `True`

#### Scenario: Delete non-existent selection

- GIVEN no selection named `"fantasma"` exists
- WHEN `delete_selection("fantasma")` is called
- THEN `selections.json` is unchanged
- AND the function returns `False`

---

### Requirement: File encoding and format

`selections.json` MUST be written with `encoding='utf-8'`, `indent=2`, and `ensure_ascii=False` to preserve special characters.
