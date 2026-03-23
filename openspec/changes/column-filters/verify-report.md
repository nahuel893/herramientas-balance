# Verification Report

**Change**: column-filters
**Version**: N/A
**Date**: 2026-03-23

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 33 (Phase 1: 2, Phase 2: 4, Phase 3: 7, Phase 4: 9, Phase 5: 12) |
| Tasks complete (Phases 1-4) | 22 |
| Tasks incomplete (Phase 5 — Smoke Tests) | 12 (require live DB) |

Phase 5 tasks are manual smoke tests requiring the live PostgreSQL DB at `100.72.221.10:5432`. These cannot be executed in CI.

**Post-apply fix**: `collectFilters()` was updated to use `querySelectorAll('input[type=checkbox]:checked')` instead of `select.selectedOptions` after the UX was changed from `<select multiple>` to checkboxes. `onGenericoChange()` was also fixed to only update the marca container instead of re-rendering all controls. Both fixes committed in `fa6c000`.

---

## Build & Tests Execution

**Build**: ✅ Passed — `python -c "from app import main"` succeeds (no build step; CDN Tailwind)

**Tests**: ➖ No automated tests exist — `openspec/config.yaml` confirms: `Testing: none currently`. Verify rule says: "No automated tests — verify manually via API endpoints or UI".

**Coverage**: ➖ Not configured

---

## Spec Compliance Matrix

### filter-values-endpoint

| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| Endpoint Route and Method | Filterable table, no cascade | `main.py:115` — `GET /api/filter-values/{table_name}` exists, returns dict of col→values | ✅ COMPLIANT (static) |
| Endpoint Route and Method | Unknown table → 400 | `main.py:117-118` — checks `table_name not in FILTERABLE_COLUMNS`, returns 400 | ✅ COMPLIANT (static) |
| Filterable Tables Config | Column not in allowlist → 400 | `main.py:124-128` — validates each query param key against `allowed_cols`, returns 400 | ✅ COMPLIANT (static) |
| Filterable Tables Config | Allowlist matches spec | `main.py:21-27` — all 5 tables with correct columns match spec exactly | ✅ COMPLIANT (static) |
| Cascade Constraints | generico filters marca | `main.py:134-136` — passes `parent_filters` (minus current col) to `get_column_values` | ✅ COMPLIANT (static) |
| Sorted Return Values | Sorted, no NULLs | `repository.py:89,92` — `ORDER BY` in SQL, `if row[0] is not None` filter | ✅ COMPLIANT (static) |
| Parameterized Queries Only | psycopg2 %s params | `repository.py:82-84,91` — uses `%s` placeholders, `cur.execute(query, params)` | ✅ COMPLIANT (static) |

### filter-model

| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| ColumnFilter Model | Valid parse | `main.py:50-52` — `ColumnFilter(BaseModel)` with `column: str`, `values: list[str]` | ✅ COMPLIANT (static) |
| ColumnFilter Model | Empty values = no filter | `services.py:43` — `if not vals: continue` skips empty values | ✅ COMPLIANT (static) |
| PreviewRequest gains filters | Backward compat | `main.py:58` — `filters: Optional[list[ColumnFilter]] = None` | ✅ COMPLIANT (static) |
| ExportRequest gains filters | Backward compat | `main.py:81` — `filters: Optional[list[ColumnFilter]] = None` | ✅ COMPLIANT (static) |

### services (delta)

| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| build_select_query removed | — | Function does not exist in services.py; replaced by `_build_conditions` | ✅ COMPLIANT (static) |
| _build_conditions — single filter | IN clause with %s | `services.py:44,52` — `', '.join(['%s'] * len(vals))` → `IN ({placeholders})` | ✅ COMPLIANT (static) |
| _build_conditions — date range | Parameterized dates | `services.py:34,36` — `f'"{date_column}" >= %s'` with `[date_from]` | ✅ COMPLIANT (static) |
| _build_conditions — fact table subquery | Subquery to dim_articulo | `services.py:45-50` — checks `FACT_TABLES` + `ARTICULO_COLUMNS`, builds subquery | ✅ COMPLIANT (static) |
| run_preview passes filters | — | `services.py:60` — accepts `filters`, passes to `_build_conditions` | ✅ COMPLIANT (static) |
| run_export passes filters | — | `services.py:82` — accepts `filters`, passes to `_build_conditions` | ✅ COMPLIANT (static) |
| No f-string of user values | — | Grep for f-string + user values returns 0 matches | ✅ COMPLIANT (static) |

### repository (delta)

| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| get_column_values | Distinct, sorted, no NULLs | `repository.py:59-94` — full implementation with `DISTINCT`, `ORDER BY`, NULL filter | ✅ COMPLIANT (static) |
| get_column_values | Cascade via dim_articulo | `repository.py:69-70` — routes to `dim_articulo` for generico/marca on fact tables | ✅ COMPLIANT (static) |
| fetch_data accepts tuples | (fragment, values) signature | `repository.py:47` — `conditions: list[tuple[str, list]]` | ✅ COMPLIANT (static) |
| fetch_data — empty conditions | No WHERE clause | `repository.py:52-53` — only adds WHERE if conditions non-empty | ✅ COMPLIANT (static) |

### frontend (delta)

| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| Static filter config | TABLE_FILTERS mirrors server | `app.js:6-29` — matches FILTERABLE_COLUMNS exactly | ✅ COMPLIANT (static) |
| Filter section renders on table select | dim_articulo → 2 controls | `app.js:67-73` — calls `loadFilterValues`, shows `filterSection` | ✅ COMPLIANT (static) |
| Table not in config → hidden | — | `app.js:70-73` — `filterSection.classList.add('hidden')` | ✅ COMPLIANT (static) |
| Cascade — generico refreshes marca | Only marca updated | `app.js:159-185` — `onGenericoChange` fetches with `?generico=X`, updates marca only | ✅ COMPLIANT (static) |
| Filters in preview POST | collectFilters included | `app.js:269-271` — `collectFilters()` → `body.filters` | ✅ COMPLIANT (static) |
| Filters in export POST | collectFilters included | `app.js:311-319` — `collectFilters()` → `body.filters` | ✅ COMPLIANT (static) |
| No filters → omitted | null check | `app.js:271,319` — `if (filters !== null) body.filters = filters` | ✅ COMPLIANT (static) |
| index.html filter placeholder | Hidden container | `index.html:72-77` — `<div id="filterSection" class="hidden">` with inner `filterControls` | ✅ COMPLIANT (static) |

**Compliance summary**: 26/26 scenarios compliant (static analysis — no automated tests exist)

---

## Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|-------------|--------|-------|
| GET /api/filter-values/{table} endpoint | ✅ Implemented | `main.py:115-138` |
| FILTERABLE_COLUMNS allowlist | ✅ Implemented | `main.py:21-27` — all 5 tables correct |
| ColumnFilter Pydantic model | ✅ Implemented | `main.py:50-52` |
| PreviewRequest.filters | ✅ Implemented | `main.py:58` |
| ExportRequest.filters | ✅ Implemented | `main.py:81` |
| get_column_values with dim_articulo routing | ✅ Implemented | `repository.py:59-94` |
| fetch_data parameterized conditions | ✅ Implemented | `repository.py:47-56` |
| _build_conditions (replaces build_select_query) | ✅ Implemented | `services.py:22-54` |
| SQL injection fixed (dates) | ✅ Implemented | `services.py:34,36` — uses `%s` params |
| Frontend filter controls (checkboxes) | ✅ Implemented | `app.js:94-156` — uses DOM createElement, not innerHTML |
| Cascade generico→marca | ✅ Implemented | `app.js:159-185` — updates only marca container |
| collectFilters with checkbox selectors | ✅ Implemented | `app.js:188-201` — uses `querySelectorAll('input[type=checkbox]:checked')` |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Allowlist in server-side FILTERABLE_COLUMNS | ✅ Yes | `main.py:21-27` |
| Subquery for generico/marca on fact tables | ✅ Yes | `services.py:45-50`, `repository.py:69-70` |
| Filter UI component | ⚠️ Deviated | Design said `<select multiple>`, implementation uses checkboxes — IMPROVEMENT (better UX, user-requested) |
| Cascade via server-side re-query | ✅ Yes | `app.js:159-185` fetches from backend |
| Params as (fragment, values) tuples | ✅ Yes | `repository.py:47`, `services.py:28,30` |
| Date filter fix in same PR | ✅ Yes | `services.py:33-36` |
| build_select_query removed | ✅ Yes | Not present in codebase; replaced by `_build_conditions` |

---

## Issues Found

**CRITICAL** (must fix before archive):
None

**WARNING** (should fix):
1. `openspec/config.yaml` context is stale — still references `silver` schema and `database.py` (should say `gold` schema and `repository.py/services.py/storage.py`). Not a code issue but misleading for future SDD phases.
2. `loadTables()` in `app.js:41-45` uses `innerHTML` with table names from the API response. While table names come from the DB schema (not user input), this is inconsistent with the safe DOM manipulation pattern used in filter controls.

**SUGGESTION** (nice to have):
1. Phase 5 smoke tests (5.1-5.12) should be validated manually against the live DB to confirm behavioral compliance.
2. `escapeHtml()` function exists in `app.js:419-426` but is no longer used after switching to DOM createElement — could be removed if no other code depends on it.

---

## Verdict

**PASS WITH WARNINGS**

All 26 spec scenarios are structurally compliant. SQL injection has been fixed across the board (dates + filters use psycopg2 `%s` params). The `<select multiple>` → checkbox deviation is a user-requested UX improvement. No automated tests exist (by project convention). Two warnings: stale openspec config and one remaining innerHTML in `loadTables()`. Phase 5 smoke tests require manual validation against live DB.
