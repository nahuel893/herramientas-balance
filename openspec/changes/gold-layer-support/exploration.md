# Exploration: gold-layer-support

## Current State

El proyecto está 100% hardcodeado al schema `silver` en tres capas:

- `app/repository.py` — 3 funciones con `silver` hardcodeado: `get_silver_tables()` (línea 19), `get_table_columns()` (línea 39), `fetch_data()` (línea 50)
- `app/services.py` — `build_select_query()` (línea 14): `FROM silver."{table}"` hardcodeado
- `app/main.py` — endpoint `/api/tables` llama `repository.get_silver_tables()`, modelos `PreviewRequest` y `ExportRequest` no tienen campo `schema`
- `app/static/app.js` — llama a `/api/tables` sin parámetro de schema
- `app/templates/index.html` — título hardcodeado "Tablas Silver"
- `app/storage.py` — selecciones guardadas no incluyen campo `schema`

## Tablas Gold disponibles (DB_CONTEXT.md)

**Dimensiones:** dim_tiempo, dim_sucursal, dim_vendedor, dim_cliente, dim_articulo, dim_deposito
**Hechos:** fact_ventas (~7M), fact_stock (~316K)
**Cobertura:** cob_preventista_marca, cob_sucursal_marca, cob_preventista_generico
**Nueva:** fact_ventas_contabilidad

## Affected Areas

| Archivo | Líneas críticas | Cambios |
|---------|-----------------|---------|
| `app/repository.py` | 19-55 | Parametrizar schema en 3 funciones |
| `app/services.py` | 14, 50-63 | Pasar schema a build_select_query y run_export |
| `app/main.py` | 26-35, 38-74 | Parámetro schema en endpoints + modelos Pydantic |
| `app/storage.py` | 15-21 | Incluir schema en save_selection |
| `app/static/app.js` | 11-20 | Selector de schema en UI |
| `app/templates/index.html` | 20, 38 | Tabs silver/gold en header |

## Approaches

### Opción A: Schema Selector en Header (Recomendada)
Dropdown/tabs global que filtra las tablas mostradas. El API recibe `schema` como query param en GET y campo en el body de POST.
- Pros: clara, evita colisiones de nombres, selecciones legibles, backward compatible
- Contras: no permite mezclar silver+gold en una selección
- Effort: Medium

### Opción B: Prefijo inline (silver.tabla / gold.tabla)
Todas las tablas listadas juntas con prefijo del schema.
- Pros: todo visible de una vez
- Contras: confuso, nombres duplicados posibles, menos legible en selecciones guardadas
- Effort: Medium

## Recommendation

**Opción A.** El usuario trabaja en un schema a la vez (report de gold = tablas gold). Selector tipo tabs en el header es UX clara y backward compatible (default = silver).

## Risks

- Backward compat: `selections.json` existente sin campo `schema` → default `silver` al leer
- CSV export: nombre del archivo no indica schema → agregar prefijo `gold_` / `silver_`
- fact_ventas en gold tiene ~7M registros → preview/export sin filtro de fecha puede ser lento
- Storage.py: selecciones guardadas antes del cambio perderían el schema si no se agrega default

## Ready for Proposal
Sí.
