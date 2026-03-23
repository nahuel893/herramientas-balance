# Verify Report: Architecture Refactor — Clean Layer Separation

**Change**: architecture-refactor
**Date**: 2026-03-18
**Verified against**: openspec/changes/architecture-refactor/specs/ + tasks.md + design.md

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 21 |
| Tasks complete | 12 |
| Tasks incomplete | 9 |

**Incomplete tasks** (Phase 4 — Smoke Tests, all require a live DB connection):

- [ ] 4.1 Start app with `python run.py` — confirm no import errors on startup
- [ ] 4.2 Call `GET /api/tables` — confirm returns `{"tables": [...]}`
- [ ] 4.3 Call `GET /api/columns/{table}` — confirm returns column metadata
- [ ] 4.4 Call `POST /api/preview` — confirm `{columns, data, count}` response
- [ ] 4.5 Call `POST /api/export` with constant column — confirm `discarded_columns` non-empty
- [ ] 4.6 Call `POST /api/export` with date_from/date_to — confirm date filtering
- [ ] 4.7 Call `POST /api/selections` + `GET /api/selections` — confirm persistence
- [ ] 4.8 Call `DELETE /api/selections/{name}` — confirm deletion
- [ ] 4.9 Call `DELETE /api/selections/nonexistent` — confirm 404 response

**Flag**: WARNING — core structural tasks (Phases 1-3) are 100% complete. Incomplete tasks are integration smoke tests that require a live PostgreSQL connection to `100.72.221.10:5432`.

---

## Build & Tests Execution

**Build**: ✅ Passed
```
$ /home/nahuel/projects/work/herramientas-balance/venv/bin/python -c "from app.main import app; print('OK')"
OK
```
All imports resolve. FastAPI app instantiates without errors.

**Tests**: ⚠️ Not configured — no test infrastructure exists yet.

Per `openspec/config.yaml`: "Testing: none currently". Per proposal: tests are out of scope for this change (tracked as `implement-testing` — next planned change that depends on this refactor).

**Coverage**: ➖ Not configured

---

## Spec Compliance Matrix

No automated tests exist. All scenarios are marked ❌ UNTESTED for behavioral compliance. Static structural evidence is noted per scenario.

### Repository spec

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| get_silver_tables | Tables exist in silver schema | (none) | ❌ UNTESTED — static: `information_schema` query with `table_schema = 'silver'` ORDER BY `table_name` present |
| get_silver_tables | No tables in silver schema | (none) | ❌ UNTESTED — static: returns `[]` from empty fetchall |
| get_table_columns | Columns retrieved for valid table | (none) | ❌ UNTESTED — static: query orders by `ordinal_position`, returns `{name, type, nullable}` dicts |
| get_table_columns | Table does not exist | (none) | ❌ UNTESTED — static: returns `[]` from empty fetchall |
| fetch_data | Fetch with no conditions | (none) | ❌ UNTESTED — static: no WHERE clause when `conditions=[]` |
| fetch_data | Fetch with date conditions | (none) | ❌ UNTESTED — static: WHERE clause built with AND-joined conditions |
| fetch_data | Empty columns list | (none) | ❌ UNTESTED — behavior unspecified by spec |
| Connection management | Close on return | (none) | ❌ UNTESTED — static: `conn.close()` called in all three functions |

### Services spec

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| build_select_query | No date filter | (none) | ❌ UNTESTED — static: pure function, returns SQL without WHERE when all date args None |
| build_select_query | Both date bounds | (none) | ❌ UNTESTED — static: both `>=` and `<=` conditions appended |
| build_select_query | Only date_from | (none) | ❌ UNTESTED — static: only `>=` condition appended |
| build_select_query | date_to with no date_column | (none) | ❌ UNTESTED — static: `if date_column and date_to` guards correctly |
| discard_unique_columns | Some columns unique | (none) | ❌ UNTESTED — static: `nunique() <= 1` check, drops and returns discarded list |
| discard_unique_columns | All columns multi-value | (none) | ❌ UNTESTED — static: empty discarded list returned |
| discard_unique_columns | Empty DataFrame | (none) | ❌ UNTESTED — static: `nunique()` on empty df returns 0 for all cols, all discarded |
| run_preview | Preview returns data | (none) | ❌ UNTESTED — static: calls `repository.fetch_data`, head(100), returns `{columns, data, count}` |
| run_export | Export with discarded columns | (none) | ❌ UNTESTED — static: `discard_unique_columns` called before `write_csv` |
| run_export | Export with date filter | (none) | ❌ UNTESTED — static: conditions built before `fetch_data` call |
| run_export | No columns discarded | (none) | ❌ UNTESTED — static: empty discarded list propagated through |

### Storage spec

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| load_selections | File exists with data | (none) | ❌ UNTESTED — static: `json.load` on existing file |
| load_selections | File does not exist | (none) | ❌ UNTESTED — static: `os.path.exists` guard, returns `{}` |
| save_selection | Save new selection | (none) | ❌ UNTESTED — static: upsert pattern with `created_at` ISO 8601 |
| save_selection | Overwrite existing | (none) | ❌ UNTESTED — static: dict key assignment overwrites |
| save_selection | File does not exist yet | (none) | ❌ UNTESTED — static: `load_selections()` returns `{}`, write creates file |
| delete_selection | Delete existing | (none) | ❌ UNTESTED — static: `del selections[name]`, returns `True` |
| delete_selection | Delete non-existent | (none) | ❌ UNTESTED — static: early return `False` when name not in dict |
| File encoding | utf-8, indent=2, ensure_ascii=False | (none) | ❌ UNTESTED — static: present in both `save_selection` and `delete_selection` write calls |

### API spec

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| GET /api/tables | Returns table list | (none) | ❌ UNTESTED — static: delegates to `repository.get_silver_tables()` |
| GET /api/columns/{table} | Returns column list | (none) | ❌ UNTESTED — static: delegates to `repository.get_table_columns()` |
| POST /api/preview | Preview with columns | (none) | ❌ UNTESTED — static: delegates to `services.run_preview()` |
| POST /api/preview | Empty columns list | (none) | ❌ UNTESTED — static: guard `if not req.columns` returns `{"error": ...}` |
| POST /api/export | Export succeeds | (none) | ❌ UNTESTED — static: delegates to `services.run_export()`, returns correct JSON shape |
| POST /api/export | Empty columns list | (none) | ❌ UNTESTED — static: guard `if not req.columns` returns `{"error": ...}` |
| GET /api/download | File exists | (none) | ❌ UNTESTED — static: `FileResponse` returned |
| GET /api/download | File not found | (none) | ❌ UNTESTED — static: `JSONResponse({"error": ...}, status_code=404)` |
| GET /api/selections | Returns all selections | (none) | ❌ UNTESTED — static: delegates to `storage.load_selections()` |
| POST /api/selections | Save selection | (none) | ❌ UNTESTED — static: delegates to `storage.save_selection()` |
| DELETE /api/selections/{name} | Delete existing | (none) | ❌ UNTESTED — static: delegates to `storage.delete_selection()`, returns `{"success": True}` |
| DELETE /api/selections/{name} | Delete non-existent | (none) | ❌ UNTESTED — static: `{"error": "Selection not found"}` when `delete_selection` returns `False` |
| main.py MUST NOT contain helper functions | No helpers defined | (none) | ✅ COMPLIANT — static: no `def load_selections` or `def save_selections` in main.py |

**Compliance summary**: 1/42 scenarios statically compliant. 41/42 untested (no test infrastructure). See Correctness section for structural evidence.

---

## Correctness (Static — Structural Evidence)

### repository.py

| Requirement | Status | Notes |
|------------|--------|-------|
| `get_connection()` using psycopg2 + env vars | ✅ Implemented | Reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` via `os.getenv` |
| `get_silver_tables()` querying information_schema | ✅ Implemented | Filters `table_schema = 'silver'`, `ORDER BY table_name` |
| `get_table_columns(table_name)` querying information_schema | ✅ Implemented | `ordinal_position` ordering, returns `{name, type, nullable}` dicts |
| `fetch_data()` building SQL with double-quoted column names | ✅ Implemented | `f'"{col}"'` escaping present |
| Connection closed before return in all functions | ✅ Implemented | `conn.close()` in `get_silver_tables`, `get_table_columns`, `fetch_data` |
| No business logic, no CSV writing, no column filtering | ✅ Implemented | Repository contains only SQL + connection logic |

### services.py

| Requirement | Status | Notes |
|------------|--------|-------|
| `build_select_query()` as PURE function (no I/O, no DB calls, no repository imports) | ✅ Implemented | Function takes only params, returns string. No I/O, no side effects. |
| `discard_unique_columns(df)` as PURE function | ✅ Implemented | Takes DataFrame, returns `(DataFrame, list[str])`. No I/O. |
| `write_csv()` with `sep=';'` and `encoding='utf-8-sig'` | ✅ Implemented | `df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')` |
| `run_preview()` calling `repository.fetch_data` | ✅ Implemented | Calls `repository.fetch_data(table, columns, [])`, then `.head(100)` |
| `run_export()` calling `repository.fetch_data` → `discard_unique_columns` → `write_csv` | ✅ Implemented | Pipeline present and correct |
| `run_export()` does NOT call `build_select_query` | ⚠️ Deviation | See design coherence section |
| No psycopg2 import | ✅ Implemented | Only imports: `pandas`, `. import repository` |

### storage.py

| Requirement | Status | Notes |
|------------|--------|-------|
| `SELECTIONS_FILE` path constant | ✅ Implemented | Absolute path computed relative to module location |
| `load_selections()` returning `{}` if file missing | ✅ Implemented | `os.path.exists` guard |
| `save_selection()` with `created_at` timestamp | ✅ Implemented | `datetime.now().isoformat()` |
| `delete_selection()` returning `bool` | ✅ Implemented | `True` if deleted, `False` if not found |
| Write with `indent=2`, `ensure_ascii=False`, `encoding='utf-8'` | ✅ Implemented | Present in both `save_selection` and `delete_selection` |

### main.py

| Requirement | Status | Notes |
|------------|--------|-------|
| Imports from `repository`, `services`, `storage` | ✅ Implemented | `from . import repository, services, storage` |
| Does NOT import from `.database` | ✅ Implemented | No `database` import present |
| Does NOT define `load_selections` or `save_selections` helpers | ✅ Implemented | No helper function definitions in main.py |
| Does NOT import `json` | ✅ Implemented | `json` not imported |
| `app/database.py` does NOT exist | ✅ Confirmed | File absent from `app/` directory |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| `build_select_query` as pure function | ✅ Yes | Pure function present, no I/O or side effects |
| `discard_unique_columns` as pure function | ✅ Yes | Pure function present, no I/O or side effects |
| `storage.py` separate from `services.py` | ✅ Yes | Separate modules, `services.py` has zero `os`/`json` imports |
| Delete `database.py`, no shim | ✅ Yes | `database.py` deleted, no re-export shim created |
| Dependency direction: `main → services → repository` | ✅ Yes | Verified via import analysis |
| `storage.py` imported only by `main.py` | ✅ Yes | `storage` not imported by `services.py` or `repository.py` |
| Data flow: `run_export` → `build_select_query` → `repository.fetch_data` | ⚠️ Deviated | `run_export` rebuilds conditions inline and calls `repository.fetch_data` directly, bypassing `build_select_query`. The pure function is defined but never called from `run_export`. |
| `run_export` return type `-> dict` (design interface table) vs `-> tuple[int, list[str], list[str]]` (spec + tasks) | ⚠️ Doc inconsistency | Implementation matches spec/tasks (returns tuple). The design's public interface table incorrectly shows `-> dict`. Not an implementation bug — design doc has a typo. |

---

## Issues Found

**CRITICAL** (must fix before archive):
None

**WARNING** (should fix):

1. **`run_export` bypasses `build_select_query`** — `services.run_export` duplicates condition-building logic that already exists in `build_select_query`, without calling it. The design data flow explicitly shows `run_export → build_select_query(...)`. This is a structural inconsistency: `build_select_query` exists as a pure, testable function but is never exercised by `run_export`. When `implement-testing` lands, tests for `run_export` will not indirectly validate `build_select_query`. The duplication is a maintenance risk — two places now build date conditions.

2. **Phase 4 smoke tests incomplete** — All 9 integration smoke tests require a live DB. They are marked incomplete and must be verified manually before archiving.

**SUGGESTION** (nice to have):

1. **Design doc typo** — `design.md` public interface table shows `run_export -> dict`, but the actual return type (matching spec/tasks) is `tuple[int, list[str], list[str]]`. Update design doc to match implementation before archiving.

2. **`run_export` could call `build_select_query`** — Refactoring `run_export` to use `build_select_query` internally would eliminate the duplicated condition-building logic and make the data flow match the design diagram exactly.

---

## Verdict

**PASS WITH WARNINGS**

The structural refactor is complete and correct. All three new modules (`repository.py`, `services.py`, `storage.py`) exist with the required functions and correct signatures. `database.py` is deleted. `main.py` is a thin controller with no embedded helpers. The import check passes cleanly. The only structural warning is that `run_export` duplicates condition logic instead of delegating to `build_select_query` as designed — this is not a behavioral bug but reduces the value of having a pure function. Phase 4 smoke tests require a live database and cannot be run in this context.
