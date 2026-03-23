# Design: Column Filters

## Technical Approach

Add dimension filters (sucursal, depósito, genérico, marca) with cascade support via a new `GET /api/filter-values/{table}` endpoint and `ColumnFilter` Pydantic model. The existing `build_select_query` is removed; query construction moves entirely into a refactored `repository.fetch_data` that receives parameterized conditions as `(fragment, values)` tuples. Date filter SQL injection is fixed in the same pass.

**Critical finding from DB_CONTEXT.md:** `fact_ventas` and `fact_stock` do NOT have `generico`/`marca` columns. Those live in `gold.dim_articulo`. Filtering fact tables by genérico/marca requires `id_articulo IN (SELECT id_articulo FROM gold."dim_articulo" WHERE "generico" = %s)` subqueries — not direct column filters. The allowlist config encodes this via a `source_table` field.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Allowlist location | Server-side `FILTERABLE_COLUMNS` dict in `main.py` | Frontend-only, DB-introspection | Prevents column-name injection; single source of truth; frontend mirrors it statically |
| Genérico/marca on fact tables | Subquery against `dim_articulo` | JOIN in main query, denormalize gold | No schema change; clean parameterization; consistent with existing no-JOIN query pattern |
| Filter UI component | `<select multiple>` | Checkboxes, tag input | Handles 27 genéricos + 98 marcas without DOM bloat; no build step required |
| Cascade execution | Server-side (backend re-query) | Load all combinations client-side | fact_ventas has 7M rows × 98 marcas — sending all combos to client is not viable |
| Params separation | `(fragment: str, values: list)` tuples | String interpolation, ORM | psycopg2 parameterization prevents injection; aligns with existing `%s` usage in `get_table_columns` |
| Date filter fix | Same PR, same refactor | Separate PR | Same injection vector; same fix pattern; leaves no half-fixed state |
| `build_select_query` removal | Delete function, inline logic in `services.py` | Keep and extend | Function only concatenated strings; its logic is superseded by the parameterized tuple approach |

## Data Flow

### GET /api/filter-values/{table}?generico=CERVEZAS

```
Browser
  │ GET /api/filter-values/fact_ventas?generico=CERVEZAS
  ▼
main.py: api_filter_values(table, query_params)
  │ validate table in FILTERABLE_COLUMNS → 400 if unknown
  │ for each filterable col: call repository.get_column_values(table, col, cascade_params)
  ▼
repository.get_column_values(table, column, parent_filters)
  │ if column in ("generico","marca") AND table is fact table:
  │   query dim_articulo directly with parent_filters as WHERE
  │ else:
  │   SELECT DISTINCT "col" FROM gold."table" WHERE {parent conditions}
  │ returns list[str] (NULLs excluded)
  ▼
main.py: returns {"generico": [...], "marca": [...]}  (marca filtered by generico cascade)
```

### POST /api/preview or /api/export with filters

```
Browser
  │ POST body: {table, columns, filters: [{column, values}], date_column, ...}
  ▼
main.py: api_preview / api_export
  │ passes filters to services.run_preview / run_export
  ▼
services.run_preview(table, columns, filters, ...)
  │ builds conditions: list[tuple[str, list]]
  │   date conditions: ("\"col\" >= %s", [date_from])
  │   dim filter on native col: ("\"col\" = ANY(%s)", [values])
  │   dim filter via subquery: ("\"id_articulo\" IN (SELECT ... WHERE \"generico\" = ANY(%s))", [values])
  ▼
repository.fetch_data(table, columns, conditions)
  │ assembles WHERE clause from condition fragments
  │ flattens params list
  │ pd.read_sql(query, conn, params=params)
  ▼
DataFrame returned to services
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/main.py` | Modify | Add `FILTERABLE_COLUMNS` dict; add `ColumnFilter` model; add `filters` field to `PreviewRequest` and `ExportRequest`; add `GET /api/filter-values/{table}` endpoint |
| `app/repository.py` | Modify | Change `fetch_data` signature to accept `conditions: list[tuple[str, list]]` and `params`; add `get_column_values(table, column, parent_filters)` function |
| `app/services.py` | Modify | Remove `build_select_query`; rewrite `run_preview` and `run_export` to build parameterized condition tuples from `filters` + date params; pass tuple list to `repository.fetch_data` |
| `app/static/app.js` | Modify | Add `TABLE_FILTERS` static config; add `renderFilterControls()`; add `fetchFilterValues(cascade_params)`; update `previewData()` and `exportData()` to collect and send `filters` array |
| `app/templates/index.html` | Modify | Add filter controls section (renders dynamically via JS); add `id="filterSection"` container before actions row |

## Interfaces / Contracts

```python
# main.py — server-side allowlist
FILTERABLE_COLUMNS = {
    "dim_articulo":             ["generico", "marca"],
    "fact_ventas":              ["id_sucursal", "generico", "marca"],
    "fact_ventas_contabilidad": ["id_sucursal", "generico", "marca"],
    "fact_stock":               ["id_deposito", "generico", "marca"],
    "dim_cliente":              ["id_sucursal"],
}

# Columns stored in dim_articulo, not directly in fact tables
ARTICULO_COLUMNS = {"generico", "marca"}
# Fact tables that reference dim_articulo via id_articulo
FACT_TABLES = {"fact_ventas", "fact_ventas_contabilidad", "fact_stock"}

# main.py — Pydantic models
class ColumnFilter(BaseModel):
    column: str     # validated against FILTERABLE_COLUMNS[table]
    values: list[str]

class PreviewRequest(BaseModel):
    table: str
    columns: list[str]
    filters: Optional[list[ColumnFilter]] = None
    date_column: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class ExportRequest(BaseModel):
    table: str
    columns: list[str]
    filters: Optional[list[ColumnFilter]] = None
    date_column: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

# repository.py — updated fetch_data signature
# conditions: list of (sql_fragment_with_%s, values_list) tuples
def fetch_data(
    table_name: str,
    columns: list[str],
    conditions: list[tuple[str, list]],
) -> pd.DataFrame: ...

def get_column_values(
    table: str,
    column: str,
    parent_filters: dict[str, list[str]],  # {col: [val,...]}
) -> list[str]: ...

# GET /api/filter-values/{table} response
# {
#   "generico": ["CERVEZAS", "VINOS", ...],
#   "marca": ["Andes", "Brahma", ...]   # filtered by cascade if ?generico=X
# }
```

```javascript
// app.js — static cascade config
const TABLE_FILTERS = {
  "dim_articulo":             [{col:"generico", label:"Genérico", cascades:"marca"}, {col:"marca", label:"Marca"}],
  "fact_ventas":              [{col:"id_sucursal", label:"Sucursal"}, {col:"generico", label:"Genérico", cascades:"marca"}, {col:"marca", label:"Marca"}],
  "fact_ventas_contabilidad": [{col:"id_sucursal", label:"Sucursal"}, {col:"generico", label:"Genérico", cascades:"marca"}, {col:"marca", label:"Marca"}],
  "fact_stock":               [{col:"id_deposito", label:"Depósito"}, {col:"generico", label:"Genérico", cascades:"marca"}, {col:"marca", label:"Marca"}],
  "dim_cliente":              [{col:"id_sucursal", label:"Sucursal"}],
}
// Each <select multiple> has id="filter-{col}"
// Empty selection = no filter applied for that column (equivalent to "Todos")
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Manual API | `/api/filter-values/dim_articulo` returns genérico list | curl or browser |
| Manual API | `?generico=CERVEZAS` on dim_articulo returns cascade-filtered marcas | curl |
| Manual API | `?generico=CERVEZAS` on fact_ventas returns correct marcas via dim_articulo subquery | curl |
| Manual API | POST preview with `filters:[{column:"generico",values:["CERVEZAS"]}]` filters rows | browser |
| Manual API | POST export applies filters; discarded-columns logic runs on filtered subset | browser |
| Security | No `%` or `'` in filter values causes SQL error (not injection) | manual test with malicious input |
| UI | Filter controls appear only for tables in TABLE_FILTERS | browser |
| UI | Selecting genérico repopulates marca without page reload | browser |

## Migration / Rollout

No migration required. No schema changes. `selections.json` format is unchanged (filters are not persisted). Rollback: `git revert` the single commit.

## Open Questions

- [ ] `fact_ventas_contabilidad` schema: confirm it also has `id_articulo` FK (assumed same pattern as `fact_ventas`). If it has `generico`/`marca` denormalized, remove it from `FACT_TABLES` set — the subquery path would not apply.
