# API Specification

## Purpose

Contract stability guarantee. All HTTP endpoints MUST retain their existing request/response shapes after the refactor. `app/main.py` becomes a thin controller layer — it MUST delegate all logic to `services` and `storage`. No behavioral change is introduced by this refactor.

## Requirements

### Requirement: GET /api/tables — unchanged

#### Scenario: Returns table list

- GIVEN the silver schema has tables
- WHEN `GET /api/tables` is called
- THEN response is `200 OK` with body `{"tables": [<string>, ...]}`

---

### Requirement: GET /api/columns/{table_name} — unchanged

#### Scenario: Returns column list

- GIVEN a valid table name
- WHEN `GET /api/columns/{table_name}` is called
- THEN response is `200 OK` with body `{"columns": [{"name": str, "type": str, "nullable": str}, ...]}`

---

### Requirement: POST /api/preview — unchanged

Request body: `{"table": str, "columns": [str, ...]}`

#### Scenario: Preview with selected columns

- GIVEN a valid table and non-empty columns list
- WHEN `POST /api/preview` is called
- THEN response body is `{"columns": [...], "data": [[...], ...], "count": int}`
- AND `count` is at most 100

#### Scenario: Empty columns list

- GIVEN `columns` is `[]`
- WHEN `POST /api/preview` is called
- THEN response body is `{"error": "No columns selected"}`

---

### Requirement: POST /api/export — unchanged

Request body: `{"table": str, "columns": [str, ...], "date_column": str|null, "date_from": str|null, "date_to": str|null}`

#### Scenario: Export succeeds

- GIVEN a valid table, non-empty columns, optional date filter
- WHEN `POST /api/export` is called
- THEN response body contains `{"filename": str, "count": int, "path": str, "exported_columns": [...], "discarded_columns": [...]}`
- AND a CSV file is written to the `exports/` directory

#### Scenario: Empty columns list

- GIVEN `columns` is `[]`
- WHEN `POST /api/export` is called
- THEN response body is `{"error": "No columns selected"}`

---

### Requirement: GET /api/download/{filename} — unchanged

#### Scenario: File exists

- GIVEN a previously exported `filename`
- WHEN `GET /api/download/{filename}` is called
- THEN response is `200 OK` with `Content-Type: text/csv` and file contents

#### Scenario: File not found

- GIVEN `filename` does not exist in `exports/`
- WHEN `GET /api/download/{filename}` is called
- THEN response is `404` with body `{"error": "File not found"}`

---

### Requirement: GET /api/selections — unchanged

#### Scenario: Returns all saved selections

- GIVEN zero or more saved selections
- WHEN `GET /api/selections` is called
- THEN response is `200 OK` with body `{"selections": {<name>: {"table": str, "columns": [...], "created_at": str}, ...}}`

---

### Requirement: POST /api/selections — unchanged

Request body: `{"name": str, "table": str, "columns": [str, ...]}`

#### Scenario: Save selection

- GIVEN a valid name, table, and columns
- WHEN `POST /api/selections` is called
- THEN response is `200 OK` with body `{"success": true}`
- AND the selection is persisted to `selections.json`

---

### Requirement: DELETE /api/selections/{name} — unchanged

#### Scenario: Delete existing selection

- GIVEN a selection named `{name}` exists
- WHEN `DELETE /api/selections/{name}` is called
- THEN response is `200 OK` with body `{"success": true}`

#### Scenario: Delete non-existent selection

- GIVEN no selection named `{name}` exists
- WHEN `DELETE /api/selections/{name}` is called
- THEN response body is `{"error": "Selection not found"}`

---

### Requirement: main.py MUST NOT contain helper functions

After the refactor, `app/main.py` MUST NOT define `load_selections`, `save_selections`, or any other non-route function. All logic MUST be delegated to `services` or `storage` modules.
