# Proposal: Architecture Refactor — Clean Layer Separation

## Intent

`database.py` viola SRP al mezclar conexión, construcción de SQL, ejecución de queries y lógica de negocio en un único módulo. `main.py` embebe helpers de persistencia que no son responsabilidad de las rutas. El resultado es código difícil de testear, mantener y extender.

Este cambio separa el código en capas con responsabilidad única, sin cambiar ningún comportamiento externo.

## Scope

### In Scope
- Crear `app/repository.py` — acceso a datos (SQL + conexión)
- Crear `app/services.py` — lógica de negocio (funciones puras + orquestadores)
- Crear `app/storage.py` — persistencia de selecciones (selections.json)
- Refactorizar `app/main.py` — eliminar helpers embebidos, rutas thin
- Eliminar `app/database.py` (reemplazado por repository.py)

### Out of Scope
- Tests (siguiente change: implement-testing — depende de este refactor)
- Connection pooling
- Manejo de errores HTTP (404, 500)
- Cambios en la API pública (endpoints, contratos JSON)
- Frontend / templates

## Approach

Separación en 4 módulos siguiendo **Single Responsibility Principle**:

```
app/
├── main.py        # HTTP in/out — thin controllers
├── repository.py  # Data access — SQL + psycopg2
├── services.py    # Business logic — pure functions + use cases
└── storage.py     # Local persistence — selections.json CRUD
```

El orden de implementación garantiza que la app siga funcionando en cada paso:
1. Crear módulos nuevos (`repository.py`, `services.py`, `storage.py`)
2. Migrar `main.py` a importar desde los nuevos módulos
3. Eliminar `database.py`

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/database.py` | Removed | Reemplazado por repository.py |
| `app/repository.py` | New | get_connection, get_silver_tables, get_table_columns, fetch_data |
| `app/services.py` | New | build_select_query (pura), discard_unique_columns (pura), run_preview, run_export, write_csv |
| `app/storage.py` | New | load_selections, save_selection, delete_selection |
| `app/main.py` | Modified | Eliminar load_selections/save_selections, actualizar imports, limpiar globals |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Romper endpoints durante migración | Low | Crear módulos nuevos primero, migrar al final |
| Regresión en lógica de descarte de columnas | Low | Comparar output de export antes/después |
| Import circular entre módulos | Low | Dependencias unidireccionales: main → services → repository |

## Rollback Plan

`database.py` se elimina al final. Si algo falla antes de ese paso, revertir los imports en `main.py` y volver a importar desde `database.py`. Git permite revertir con `git checkout app/main.py app/database.py`.

## Dependencies

- Ninguna dependencia externa nueva — refactor puro con el stack actual

## Success Criteria

- [ ] `app/database.py` eliminado
- [ ] `app/repository.py` creado con funciones de acceso a datos
- [ ] `app/services.py` creado con `build_select_query` y `discard_unique_columns` como funciones puras
- [ ] `app/storage.py` creado con CRUD de selecciones
- [ ] `app/main.py` sin helpers embebidos — solo rutas y serialización
- [ ] Todos los endpoints responden igual que antes (mismo contrato JSON)
- [ ] La app arranca con `python run.py` sin errores
