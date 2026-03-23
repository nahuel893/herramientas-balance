# Tasks: Column Filters

## Phase 1: Repository Layer

- [x] 1.1 In `app/repository.py`, change `fetch_data` signature from `conditions: list[str]` to `conditions: list[tuple[str, list]]` and flatten params via `[v for _, vals in conditions for v in vals]`; call `pd.read_sql(query, conn, params=params)` — NOT f-strings. Empty conditions must produce no WHERE clause.
- [x] 1.2 In `app/repository.py`, add `get_column_values(table: str, column: str, parent_filters: list) -> list` function. If `column in {"generico", "marca"}` AND `table in {"fact_ventas", "fact_ventas_contabilidad", "fact_stock"}`, query `gold."dim_articulo"` directly (not the fact table) with parent_filters as parameterized WHERE conditions. Otherwise query `gold."<table>"` directly. Exclude NULLs; sort results; return list of strings. All filter values via `%s` params — no f-strings.

## Phase 2: Services Layer

- [x] 2.1 In `app/services.py`, remove the `build_select_query()` function entirely.
- [x] 2.2 In `app/services.py`, update `run_preview(table, columns)` to accept `filters: list | None = None`. Build conditions as `list[tuple[str, list]]`. For each `ColumnFilter` with non-empty values: if `column in {"generico","marca"}` AND `table in FACT_TABLES`, emit `("\"id_articulo\" IN (SELECT id_articulo FROM gold.\"dim_articulo\" WHERE \"{col}\" = ANY(%s))", [values])`; otherwise emit `("\"{col}\" = ANY(%s)", [values])`. Pass conditions to `repository.fetch_data`. Apply `.head(100)` after fetch.
- [x] 2.3 In `app/services.py`, update `run_export(table, columns, output_path, date_column, date_from, date_to)` to accept `filters: list | None = None`. Build conditions the same way as `run_preview`. Fix date filter injection: replace f-string `conditions.append(f'"{date_column}" >= \'{date_from}\'')` with parameterized tuple `conditions.append(('"<col>" >= %s', [date_from]))`. Pass full conditions list to `repository.fetch_data`. `discard_unique_columns` still runs on the resulting DataFrame.
- [x] 2.4 Verify `app/services.py` has zero f-string interpolation of user-supplied values (date strings, filter values). Column names from the app's own schema remain double-quoted via f-strings — that is acceptable.

## Phase 3: Main / API Layer

- [x] 3.1 In `app/main.py`, add module-level constants: `FILTERABLE_COLUMNS` dict (5 tables as per design), `FACT_TABLES = {"fact_ventas", "fact_ventas_contabilidad", "fact_stock"}`, `ARTICULO_COLUMNS = {"generico", "marca"}`.
- [x] 3.2 In `app/main.py`, add `ColumnFilter(BaseModel)` with `column: str` and `values: list[str]` fields.
- [x] 3.3 In `app/main.py`, add `filters: Optional[list[ColumnFilter]] = None` to `PreviewRequest`. Existing `table` and `columns` fields remain unchanged. Backward-compatible: missing `filters` defaults to `None`.
- [x] 3.4 In `app/main.py`, add `filters: Optional[list[ColumnFilter]] = None` to `ExportRequest`. Existing `table`, `columns`, `date_column`, `date_from`, `date_to` fields remain unchanged.
- [x] 3.5 In `app/main.py`, add `GET /api/filter-values/{table}` endpoint. Validate `table` in `FILTERABLE_COLUMNS` → 400 if not. Validate each query param key against the table's allowlist → 400 if unknown column passed. For each allowed column, call `repository.get_column_values(table, col, cascade_filters)` where `cascade_filters` are the validated query params. Return `{col: [values...]}` dict.
- [x] 3.6 In `app/main.py`, update `api_preview` to pass `req.filters` to `services.run_preview`.
- [x] 3.7 In `app/main.py`, update `api_export` to pass `req.filters` to `services.run_export`.

## Phase 4: Frontend

- [x] 4.1 In `app/static/app.js`, add `TABLE_FILTERS` constant (object) before any function definitions. Keys: `dim_articulo`, `fact_ventas`, `fact_ventas_contabilidad`, `fact_stock`, `dim_cliente`. Each value is an array of filter descriptor objects `{col, label, cascades?}` matching the design spec.
- [x] 4.2 In `app/static/app.js`, add `loadFilterValues(table, cascadeParams = {})` async function. Builds query string from `cascadeParams`. Calls `GET /api/filter-values/{table}?...`. On response, calls `renderFilterControls(table, data)`.
- [x] 4.3 In `app/static/app.js`, add `renderFilterControls(table, valuesData)` function. Uses `TABLE_FILTERS[table]` to render one `<select multiple id="filter-{col}">` per column populated from `valuesData[col]`. Adds `onchange` on `generico` select to call `onGenericoChange(table)`. Hides `#filterSection` if table not in `TABLE_FILTERS`.
- [x] 4.4 In `app/static/app.js`, add `onGenericoChange(table)` function. Reads selected values from `#filter-generico`. Calls `loadFilterValues(table, {generico: selectedValues})` to cascade-reload marca. Clears marca selection before repopulate.
- [x] 4.5 In `app/static/app.js`, update `selectTable(tableName)` to call `loadFilterValues(tableName)` if `tableName in TABLE_FILTERS`, else hide `#filterSection` and clear all filter state.
- [x] 4.6 In `app/static/app.js`, add `collectFilters()` helper. Iterates `TABLE_FILTERS[currentTable]`, reads selected values from each `#filter-{col}` select, returns `[{column, values}]` array omitting entries with zero selected values. Returns `null` if result is empty.
- [x] 4.7 In `app/static/app.js`, update `previewData()` to call `collectFilters()` and include `filters` in the POST body (omit key if `null`).
- [x] 4.8 In `app/static/app.js`, update `exportData()` to call `collectFilters()` and include `filters` in the POST body (omit key if `null`).
- [x] 4.9 In `app/templates/index.html`, add `<div id="filterSection" class="hidden">` container with an inner `<div id="filterControls">` before the actions row (Preview / Export buttons). JS injects dropdowns into `#filterControls` and toggles `hidden` on `#filterSection`.

## Phase 5: Smoke Test

- [ ] 5.1 `GET /api/filter-values/dim_articulo` returns 200 with `generico` and `marca` keys, both sorted lists, no NULLs.
- [ ] 5.2 `GET /api/filter-values/dim_articulo?generico=CERVEZAS` returns only marcas that exist for CERVEZAS in `dim_articulo`.
- [ ] 5.3 `GET /api/filter-values/fact_ventas?generico=CERVEZAS` returns marcas via dim_articulo subquery path (confirm by checking that `fact_ventas` has no `generico` column).
- [ ] 5.4 `GET /api/filter-values/fact_unknown` returns 400.
- [ ] 5.5 `GET /api/filter-values/fact_ventas?nombre=X` returns 400 (column not in allowlist).
- [ ] 5.6 `POST /api/preview` without `filters` key still works (backward compat).
- [ ] 5.7 `POST /api/preview` with `filters:[{column:"generico",values:["CERVEZAS"]}]` on `dim_articulo` returns only CERVEZAS rows.
- [ ] 5.8 `POST /api/export` with filters produces CSV containing only filtered rows; discarded-columns logic still runs on filtered subset.
- [ ] 5.9 Browser: select `dim_articulo`, verify filter section appears with generico and marca dropdowns.
- [ ] 5.10 Browser: select a generico value, verify marca dropdown repopulates without page reload.
- [ ] 5.11 Browser: switch to a table not in `TABLE_FILTERS`, verify filter section hides and previous filter values are cleared.
- [ ] 5.12 Manual security: send `GET /api/filter-values/dim_articulo?generico='; DROP TABLE gold.dim_articulo; --` — must return empty list or error, NOT execute SQL.
