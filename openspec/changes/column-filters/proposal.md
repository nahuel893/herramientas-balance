# Proposal: Column Filters

## Intent

Users need to filter data by business dimensions (sucursal, generico, marca, deposito) before preview and export. Currently only date filters exist, and even those use f-string interpolation — a SQL injection vulnerability. This change adds dimension filters with cascade support and fixes the injection vector across the board.

## Scope

### In Scope
- New `GET /api/filter-values/{table}` endpoint returning distinct filterable column values with optional cascade constraints
- New `ColumnFilter` Pydantic model; `filters` field added to `PreviewRequest` and `ExportRequest`
- `build_select_query()` updated to apply `ColumnFilter` list as parameterized IN clauses
- `run_preview()` updated to accept and pass filters (currently hardcodes `[]`)
- `run_export()` updated to accept and pass filters
- Fix existing date filter SQL injection (f-string → psycopg2 params)
- Dynamic filter UI in frontend: renders per-table filter controls; generico → marca cascade triggers backend refresh
- New `get_column_values()` function in `repository.py`

### Out of Scope
- Multi-select UI components (standard `<select multiple>` acceptable)
- Saving filter state to `selections.json`
- Numeric range filters (min/max)
- Filters on tables not listed in the per-table config

## Approach

**Backend:** Add `GET /api/filter-values/{table}` that accepts query params as cascade constraints (e.g. `?generico=CERVEZAS`). It calls a new `repository.get_column_values(table, column, parent_filters)` that builds a `SELECT DISTINCT` with psycopg2 `%s` params. `build_select_query()` is refactored to receive `filters: list[ColumnFilter]` and emit `"col" = ANY(%s)` or `"col" IN %s` clauses — all parameterized. The date filter conditions are moved to params at the same time.

**Frontend:** A static config object maps each table to its filterable columns and cascade order. On table select, filter UI renders. On generico change, JS calls `/api/filter-values/{table}?generico=X` and repopulates the marca dropdown. Preview and export POSTs include the `filters` array.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/main.py` | Modified | New endpoint + expanded Pydantic models |
| `app/repository.py` | Modified | New `get_column_values()` function |
| `app/services.py` | Modified | `build_select_query`, `run_preview`, `run_export` — add filters, fix SQL injection |
| `app/static/app.js` | Modified | Filter UI logic, cascade fetch, include filters in requests |
| `app/templates/index.html` | Modified | Filter section HTML |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| SQL injection via filter values | High (currently) | All filter values MUST use psycopg2 `%s` params — no f-strings |
| Performance on fact_ventas (7M rows) | Med | `DISTINCT` queries on indexed columns (id_sucursal, generico) are fast; unindexed marca may be slow — acceptable for UX |
| NULL values in filterable columns | Med | `SELECT DISTINCT` includes NULLs; frontend drops null entries from dropdown |
| Column name injection via `column` param | Med | Allowlist of valid filter columns per table — reject unknowns with 400 |

## Rollback Plan

Git revert the commit that introduces this change. No schema migrations involved. `selections.json` format is unchanged.

## Dependencies

None — no new packages required. psycopg2 parameterization is already available.

## Success Criteria

- [ ] `/api/filter-values/dim_articulo` returns distinct generico values
- [ ] `/api/filter-values/dim_articulo?generico=CERVEZAS` returns only marcas for that generico
- [ ] Preview with `filters: [{column: "generico", values: ["CERVEZAS"]}]` returns only matching rows
- [ ] Export applies same filters; discarded-columns logic still works on filtered data
- [ ] No f-string interpolation of user input anywhere in services.py or repository.py
- [ ] Frontend renders filter controls for dim_articulo, fact_ventas, fact_ventas_contabilidad, fact_stock, dim_cliente
- [ ] Selecting generico refreshes marca dropdown without page reload
