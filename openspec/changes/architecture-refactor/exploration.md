# Exploration: architecture-refactor

## Current State

El proyecto tiene 2 módulos Python activos:

### `app/database.py` — 77 líneas, hace todo
- `get_connection()` — crea una conexión psycopg2 nueva por cada llamada (sin pool)
- `get_silver_tables()` — query a information_schema
- `get_table_columns(table_name)` — query a information_schema
- `preview_data(table_name, columns, limit)` — construye SQL + ejecuta + retorna DataFrame
- `export_data(table_name, columns, output_path, ...)` — construye SQL + ejecuta + **aplica lógica de negocio** (descarta columnas con 1 valor único) + escribe CSV

`export_data` tiene 5 responsabilidades distintas en una función de 25 líneas.

### `app/main.py` — 130 líneas, mezcla rutas con lógica de infraestructura
- Rutas FastAPI (lo correcto)
- `load_selections()` / `save_selections()` — helpers de persistencia embebidos (incorrecto)
- Construcción de `SELECTIONS_FILE` y `EXPORTS_DIR` como globals (mezclado con rutas)
- Construcción de filename/filepath en el handler de export (lógica de negocio en la ruta)

## Problemas Concretos

| Problema | Archivo | Líneas |
|----------|---------|--------|
| Lógica de negocio en capa de datos | `database.py` | 69-73 |
| Construcción SQL mezclada con ejecución | `database.py` | 53-63 |
| Persistencia de selecciones en main.py | `main.py` | 22-30 |
| Paths de infraestructura como globals en rutas | `main.py` | 19-20 |
| Sin pool de conexiones | `database.py` | 8-15 |
| Sin manejo de errores en DB | `database.py` | todas |

## Affected Areas

- `app/database.py` — split en `repository.py` + lógica de negocio a `services.py`
- `app/main.py` — extraer storage a `storage.py`, limpiar rutas
- `app/__init__.py` — sin cambios
- `requirements.txt` — agregar `pytest`, `httpx` (para testing posterior)
- Nuevo: `app/repository.py`, `app/services.py`, `app/storage.py`

## Arquitectura Propuesta

```
app/
├── main.py        # Rutas únicamente — controllers thin
├── repository.py  # SQL + conexión psycopg2 — data access layer
├── services.py    # Lógica de negocio — use cases + funciones puras
└── storage.py     # Persistencia selections.json — infraestructura local
```

### Responsabilidades por módulo

**`repository.py`**
- `get_connection()` — gestión de conexión
- `get_silver_tables() -> list[str]`
- `get_table_columns(table_name) -> list[dict]`
- `fetch_data(table_name, columns, conditions) -> DataFrame` — solo ejecuta, sin transformar

**`services.py`** (funciones puras testeables + orquestadores)
- `build_select_query(table, columns, date_column, date_from, date_to) -> str` — PURA
- `discard_unique_columns(df) -> tuple[DataFrame, list[str]]` — PURA
- `write_csv(df, output_path) -> None`
- `run_preview(table, columns) -> dict`
- `run_export(table, columns, output_path, ...) -> dict`

**`storage.py`**
- `load_selections() -> dict`
- `save_selection(name, table, columns) -> None`
- `delete_selection(name) -> None`

**`main.py`** — solo routing y serialización HTTP

## Recommendation

Separación en 4 módulos siguiendo Single Responsibility Principle. El beneficio inmediato es que `services.py` es 100% testeable sin DB (funciones puras). El beneficio arquitectónico es que cada capa puede evolucionar independientemente.

## Risks

- El refactor es un cambio de estructura sin cambio de comportamiento — riesgo bajo si se hace en orden correcto
- Hay que mantener la app funcionando durante el refactor (sin romper endpoints)
- `get_connection()` sin pool no es problema hoy pero sí en el futuro si escala

## Ready for Proposal
Sí.
