# Tasks: Migrate to Gold Schema

## Phase 1: Backend — Python changes

- [x] 1.1 In `app/repository.py` line 19: rename function `get_silver_tables()` → `get_tables()`
- [x] 1.2 In `app/repository.py` line 25: replace `WHERE table_schema = 'silver'` → `'gold'` (tables query)
- [x] 1.3 In `app/repository.py` line 39: replace `WHERE table_schema = 'silver'` → `'gold'` (columns query)
- [x] 1.4 In `app/repository.py` line 50: replace `FROM silver."{table_name}"` → `FROM gold."{table_name}"`
- [x] 1.5 In `app/services.py` line 14: replace `FROM silver."{table}"` → `FROM gold."{table}"` in `build_select_query()`
- [x] 1.6 In `app/main.py` line 12: replace `FastAPI(title="Silver Column Selector")` → `FastAPI(title="Gold Column Selector")`
- [x] 1.7 In `app/main.py` line 28: replace `repository.get_silver_tables()` → `repository.get_tables()`

## Phase 2: Frontend — HTML label changes

- [x] 2.1 In `app/templates/index.html` line 6: replace `<title>Silver Column Selector</title>` → `<title>Gold Column Selector</title>`
- [x] 2.2 In `app/templates/index.html` line 20: replace `Silver Column Selector` → `Gold Column Selector` in `<h1>`
- [x] 2.3 In `app/templates/index.html` line 38: replace `<h2 ...>Tablas Silver</h2>` → `<h2 ...>Tablas</h2>`

## Phase 3: Installer — selections.json reset

- [x] 3.1 In `install.bat`, after the `if not exist exports mkdir exports` line (line 26), add reset block: `echo {} > selections.json` with a comment explaining silver selections are invalid against gold schema

## Phase 4: Docs — CLAUDE.md update

- [x] 4.1 In `CLAUDE.md`, update `## Proyecto` section: replace "tablas Silver" → "tablas Gold"
- [x] 4.2 In `CLAUDE.md`, update `Schema principal:` from `silver` to `gold`
- [x] 4.3 In `CLAUDE.md`, update `Estructura` section: replace `database.py` reference with `repository.py` and `services.py`
- [x] 4.4 In `CLAUDE.md`, update endpoint table: replace `/api/tables` description from "Lista tablas silver" → "Lista tablas gold"

## Phase 5: Smoke test — manual verification

- [ ] 5.1 Start the app with `python run.py` and verify it starts without errors
- [ ] 5.2 `curl http://localhost:8000/api/tables` — response must contain gold table names (e.g. `dim_tiempo`, `fact_ventas`)
- [ ] 5.3 `curl http://localhost:8000/api/columns/dim_sucursal` — response must return columns without error
- [ ] 5.4 Open browser at `http://localhost:8000` — header must show "Gold Column Selector", left panel must show "Tablas" (not "Tablas Silver")
- [ ] 5.5 Select columns from a gold table, click Preview — data must load without SQL error
- [ ] 5.6 Export a gold table to CSV — file must be created in `exports/` with correct `;` separator
- [ ] 5.7 Run `install.bat` and verify `selections.json` contains `{}` after execution
- [ ] 5.8 Confirm no remaining `silver` references in Python source: search `app/` for the string `silver`
