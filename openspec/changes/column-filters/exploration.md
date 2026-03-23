# Exploration: column-filters

## Current State

Solo existe filtro de fecha (date_column / date_from / date_to) en PreviewRequest y ExportRequest.
No hay endpoint para obtener valores distintos de una columna.
`run_preview()` en services.py pasa `[]` como conditions — ignora filtros por completo.

## Nombres exactos de columnas de filtro en gold

| Tabla | Filtros | Columnas exactas |
|-------|---------|-----------------|
| `dim_articulo` | generico → marca (cascada) | `generico`, `marca` |
| `fact_ventas` | sucursal, generico, marca | `id_sucursal`, `generico`, `marca` |
| `fact_ventas_contabilidad` | sucursal, generico, marca | `id_sucursal`, `generico`, `marca` |
| `fact_stock` | deposito, generico, marca | `id_deposito`, `generico`, `marca` |
| `dim_cliente` | sucursal | `id_sucursal` |

Nota: en fact_ventas y fact_stock, `generico` y `marca` pueden estar directamente como columnas en gold (schema dimensional denormalizado), o requerir JOIN con dim_articulo. Verificar en DB_CONTEXT.md.

## Cómo funcionan los filtros de fecha actuales

1. Frontend envía `date_column`, `date_from`, `date_to` en body del POST
2. `services.build_select_query()` agrega condiciones con f-strings (vulnerabilidad SQL injection — pendiente fijar)
3. `repository.fetch_data(table, columns, conditions)` ejecuta con WHERE

## Approach elegido: Filtros con Cascada + Endpoint de Valores (Approach 2)

El usuario pidió cascada explícitamente (generico → marca).

### Nuevo endpoint
```
GET /api/filter-values/{table}?filters=generico:CERVEZAS
```
Retorna valores distintos de columnas de filtro, con soporte de cascada.

### Modelo de datos
```python
class ColumnFilter(BaseModel):
    column: str
    values: list[str]  # valores seleccionados (IN clause)

class PreviewRequest(BaseModel):
    table: str
    columns: list[str]
    filters: Optional[list[ColumnFilter]] = None
    date_column: Optional[str] = None
    ...

class ExportRequest(BaseModel):
    ... mismo patrón
```

### Filtros por tabla (UX: render dinámico según tabla seleccionada)
La UI renderiza la sección de filtros según la tabla activa. Configuración en frontend.

## Affected Areas

| Archivo | Cambios |
|---------|---------|
| `app/main.py` | Nuevo endpoint `/api/filter-values/{table}`, expandir modelos Pydantic |
| `app/repository.py` | Nueva función `get_column_values(table, column, parent_filters)` |
| `app/services.py` | Expandir `build_select_query` y `run_preview` para soportar `filters` |
| `app/static/app.js` | Nueva UI de filtros + lógica de cascada + pasar filters en requests |
| `app/templates/index.html` | Sección de filtros dinámica |

## Risks

- SQL injection: filtros de columna DEBEN usar psycopg2 `%s` parametrizado (NO f-strings)
- Performance: fact_ventas 7M filas — filtrar sin índice puede ser lento
- Preview actualmente ignora conditions — cambio a "preview sí filtra"
- Valores NULL en columnas filtrables

## Ready for Proposal
Sí.
