# Tasks: Architecture Refactor — Clean Layer Separation

## Phase 1: Create New Modules

- [ ] 1.1 Create `app/repository.py` — implement `get_connection()` extracting psycopg2 connect logic verbatim from `database.py` (repository/connection-management)
- [ ] 1.2 Add `get_silver_tables() -> list[str]` to `app/repository.py` — extract verbatim from `database.py`, open+close connection per call (repository/get_silver_tables)
- [ ] 1.3 Add `get_table_columns(table_name: str) -> list[dict]` to `app/repository.py` — extract verbatim from `database.py`, return dicts with `name`, `type`, `nullable` keys (repository/get_table_columns)
- [ ] 1.4 Add `fetch_data(table_name: str, columns: list[str], conditions: list[str]) -> DataFrame` to `app/repository.py` — accepts pre-built conditions list, no query building (repository/fetch_data)
- [ ] 1.5 Create `app/services.py` — implement `build_select_query(table, columns, date_column, date_from, date_to) -> str` as pure function, column names double-quoted (services/build_select_query)
- [ ] 1.6 Add `discard_unique_columns(df: DataFrame) -> tuple[DataFrame, list[str]]` to `app/services.py` — pure function, extract from `export_data` in `database.py` (services/discard_unique_columns)
- [ ] 1.7 Add `write_csv(df: DataFrame, output_path: str) -> None` to `app/services.py` — `sep=';'`, `encoding='utf-8-sig'`, `index=False` (services/run_export)
- [ ] 1.8 Add `run_preview(table: str, columns: list[str]) -> dict` to `app/services.py` — calls `repository.fetch_data` with empty conditions, returns `{columns, data, count}`, max 100 rows (services/run_preview)
- [ ] 1.9 Add `run_export(table, columns, output_path, date_column, date_from, date_to) -> tuple[int, list[str], list[str]]` to `app/services.py` — orchestrates `build_select_query` → `fetch_data` → `discard_unique_columns` → `write_csv` (services/run_export)
- [ ] 1.10 Create `app/storage.py` — implement `load_selections() -> dict` returning `{}` if file missing (storage/load_selections)
- [ ] 1.11 Add `save_selection(name: str, table: str, columns: list[str]) -> None` to `app/storage.py` — loads, upserts entry with `table`, `columns`, `created_at` (ISO 8601), writes with `indent=2`, `ensure_ascii=False` (storage/save_selection)
- [ ] 1.12 Add `delete_selection(name: str) -> bool` to `app/storage.py` — returns `True` if deleted, `False` if not found (storage/delete_selection)

## Phase 2: Migrate main.py

- [ ] 2.1 Replace `from .database import get_silver_tables, get_table_columns, preview_data, export_data` with imports from `repository`, `services`, and `storage` in `app/main.py` (api/unchanged contract)
- [ ] 2.2 Update `api_tables()` route to call `repository.get_silver_tables()` (api/GET /api/tables)
- [ ] 2.3 Update `api_columns()` route to call `repository.get_table_columns()` (api/GET /api/columns)
- [ ] 2.4 Update `api_preview()` route to call `services.run_preview()` — remove inline DataFrame handling (api/POST /api/preview)
- [ ] 2.5 Update `api_export()` route to call `services.run_export()` — keep timestamp/filename logic in main (api/POST /api/export)
- [ ] 2.6 Update `api_get_selections()` to call `storage.load_selections()` (api/GET /api/selections)
- [ ] 2.7 Update `api_save_selection()` to call `storage.save_selection()` — remove inline dict construction and `save_selections` call (api/POST /api/selections)
- [ ] 2.8 Update `api_delete_selection()` to call `storage.delete_selection()` — remove inline load/delete/save pattern (api/DELETE /api/selections)
- [ ] 2.9 Remove `load_selections` and `save_selections` helper functions from `app/main.py` (api/main.py MUST NOT contain helper functions)
- [ ] 2.10 Remove `import json` from `app/main.py` if no longer used after helpers are removed

## Phase 3: Delete database.py

- [ ] 3.1 Verify `app/main.py` has no remaining references to `.database` (any grep/search)
- [ ] 3.2 Delete `app/database.py`

## Phase 4: Smoke Test

- [ ] 4.1 Start app with `python run.py` — confirm no import errors on startup
- [ ] 4.2 Call `GET /api/tables` — confirm returns `{"tables": [...]}` with same list as before
- [ ] 4.3 Call `GET /api/columns/{table}` — confirm returns `{"columns": [{name, type, nullable}, ...]}` for a known table
- [ ] 4.4 Call `POST /api/preview` with a valid table and columns — confirm `{"columns", "data", "count"}` response, count <= 100
- [ ] 4.5 Call `POST /api/export` with a table that has a constant column — confirm `discarded_columns` is non-empty and CSV matches exported columns
- [ ] 4.6 Call `POST /api/export` with date_from/date_to — confirm CSV rows are within the date range
- [ ] 4.7 Call `POST /api/selections`, then `GET /api/selections` — confirm saved entry appears with `table`, `columns`, `created_at`
- [ ] 4.8 Call `DELETE /api/selections/{name}` — confirm `{"success": true}` and entry is absent from subsequent `GET`
- [ ] 4.9 Call `DELETE /api/selections/nonexistent` — confirm `{"error": "Selection not found"}`
