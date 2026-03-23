# Design: Migrate to Gold Schema

## Technical Approach

Direct string replacement of `silver` → `gold` across 4 source files plus a UI label update and a `selections.json` reset in `install.bat`. No new parameters, no schema selector, no architectural changes. The app will target `gold` exclusively after this change.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Replace vs extend | Replace (gold-only) | Multi-schema selector | User explicitly chose gold-only; no backward compat needed; keeps codebase minimal |
| Function rename | `get_silver_tables()` → `get_tables()` | Keep old name | Single caller in `main.py`; rename removes schema leak from public interface |
| Where to reset `selections.json` | `install.bat` | `start.bat` | `install.bat` is deploy-time; `start.bat` runs on every launch — resetting there would destroy user selections each restart |
| How to reset `selections.json` | Overwrite with `{}` via `echo {} > selections.json` | Delete file | Overwrite is atomic for a Windows batch; avoids race condition if app starts before file is recreated by first write |
| No `schema` parameter | No param added anywhere | Add `schema` query/body param | Gold is the only schema; adding a param adds complexity with no current benefit |

## Data Flow

```
Browser → GET /api/tables
              ↓
         main.py: api_tables()
              ↓
         repository.get_tables()          ← renamed
              ↓
         SELECT table_name
         FROM information_schema.tables
         WHERE table_schema = 'gold'      ← changed
              ↓
         [dim_tiempo, dim_sucursal, fact_ventas, ...]

Browser → POST /api/preview  /  POST /api/export
              ↓
         services.run_preview() / run_export()
              ↓
         repository.fetch_data()
              ↓
         SELECT ... FROM gold."{table}"   ← changed
```

## File Changes

| File | Action | What changes |
|------|--------|--------------|
| `app/repository.py` | Modify | Rename `get_silver_tables` → `get_tables`; replace `'silver'` with `'gold'` in 3 places (lines 19, 25, 39, 50) |
| `app/services.py` | Modify | Replace `FROM silver."{table}"` → `FROM gold."{table}"` (line 14) |
| `app/main.py` | Modify | Update call `repository.get_silver_tables()` → `repository.get_tables()` (line 28); update `FastAPI(title=...)` string |
| `app/templates/index.html` | Modify | `<title>` line 6; `<h1>` line 20; `<h2>` line 38 — remove "Silver" references |
| `install.bat` | Modify | Add reset block for `selections.json` (overwrite with `{}`) after exports dir creation |
| `CLAUDE.md` | Modify | Schema principal: `silver` → `gold`; update description and endpoint table |

## Interfaces / Contracts

No interface changes. All endpoints, request/response shapes, and Pydantic models remain identical. The only observable contract change is that `/api/tables` now returns gold table names (`dim_tiempo`, `fact_ventas`, etc.) instead of silver names.

## Exact String Replacements

### `app/repository.py`

```python
# Line 19 — rename function
def get_silver_tables() -> list[str]:   →   def get_tables() -> list[str]:

# Line 25 — schema in query
WHERE table_schema = 'silver'           →   WHERE table_schema = 'gold'

# Line 39 — schema in columns query
WHERE table_schema = 'silver' AND       →   WHERE table_schema = 'gold' AND

# Line 50 — schema in fetch_data
FROM silver."{table_name}"              →   FROM gold."{table_name}"
```

### `app/services.py`

```python
# Line 14 — schema in build_select_query
FROM silver."{table}"                   →   FROM gold."{table}"
```

### `app/main.py`

```python
# Line 12 — app title
FastAPI(title="Silver Column Selector") →   FastAPI(title="Gold Column Selector")

# Line 28 — function call
repository.get_silver_tables()          →   repository.get_tables()
```

### `app/templates/index.html`

```html
<!-- Line 6 -->
<title>Silver Column Selector</title>   →   <title>Gold Column Selector</title>

<!-- Line 20 -->
Silver Column Selector                  →   Gold Column Selector

<!-- Line 38 -->
<h2 ...>Tablas Silver</h2>              →   <h2 ...>Tablas</h2>
```

### `install.bat`

Add after the `if not exist exports mkdir exports` block:

```bat
:: Reset selections (silver selections are invalid against gold schema)
echo {} > selections.json
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Manual — API | `/api/tables` returns gold table names | `curl http://localhost:8000/api/tables` |
| Manual — API | `/api/columns/dim_cliente` returns columns | `curl http://localhost:8000/api/columns/dim_cliente` |
| Manual — UI | Title shows "Gold Column Selector" | Open browser, verify header |
| Manual — UI | Table panel shows gold tables | Open browser, check left panel |
| Manual — Export | Preview and CSV export work against a gold table | Select columns from `dim_sucursal`, preview and export |
| Manual — install | `selections.json` is `{}` after running `install.bat` | Inspect file after install |

## Migration / Rollout

`selections.json` is reset to `{}` by `install.bat`. Existing silver selections become invalid (gold table names differ, e.g. `clientes` → `dim_cliente`) — this is intentional and handled by the reset. No database migration required — gold schema already exists in `medallion_db`.

## Open Questions

- None. All decisions resolved per proposal.
