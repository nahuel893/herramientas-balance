# filter-values-endpoint Specification

## Purpose

New endpoint that returns distinct values for filterable columns of a given table, with optional cascade constraints via query parameters.

## Requirements

### Requirement: Endpoint Route and Method

The system MUST expose `GET /api/filter-values/{table}` in `app/main.py`.

#### Scenario: Request for a filterable table with no cascade

- GIVEN the table `dim_articulo` is in the filterable tables config
- WHEN a client sends `GET /api/filter-values/dim_articulo`
- THEN the response MUST be `200 OK` with a JSON object mapping each filterable column to its sorted distinct values
- AND the response MUST include both `generico` and `marca` keys

#### Scenario: Request for an unknown table

- GIVEN the table `fact_unknown` is NOT in the filterable tables config
- WHEN a client sends `GET /api/filter-values/fact_unknown`
- THEN the response MUST be `400 Bad Request`
- AND the error body MUST indicate the table is not filterable

### Requirement: Filterable Tables Config

The system MUST enforce the following server-side allowlist:

| Table | Allowed filter columns |
|-------|----------------------|
| `dim_articulo` | `generico`, `marca` |
| `fact_ventas` | `id_sucursal`, `generico`, `marca` |
| `fact_ventas_contabilidad` | `id_sucursal`, `generico`, `marca` |
| `fact_stock` | `id_deposito`, `generico`, `marca` |
| `dim_cliente` | `id_sucursal` |

#### Scenario: Column not in allowlist passed as query param

- GIVEN `fact_ventas` is a filterable table
- WHEN a client sends `GET /api/filter-values/fact_ventas?nombre=X`
- THEN the response MUST be `400 Bad Request`
- AND the error MUST indicate `nombre` is not a valid filter column for `fact_ventas`

### Requirement: Cascade Constraints via Query Parameters

The system MUST accept query parameters that constrain child column values. Each query param key MUST be a column in the allowlist for that table.

#### Scenario: Cascade — generico filters marca

- GIVEN `dim_articulo` has rows with `generico='CERVEZAS'` and `marca` values `['BRAHMA', 'CORONA']`
- WHEN a client sends `GET /api/filter-values/dim_articulo?generico=CERVEZAS`
- THEN the response MUST return only marcas that exist for `generico='CERVEZAS'`
- AND other generico values MUST still be returned unconstrained

#### Scenario: Multiple cascade params

- GIVEN `fact_ventas` has filterable columns `id_sucursal`, `generico`, `marca`
- WHEN a client sends `GET /api/filter-values/fact_ventas?id_sucursal=5&generico=CERVEZAS`
- THEN `marca` values MUST be filtered to those existing for that `id_sucursal` AND `generico` combination
- AND `id_sucursal` and `generico` distinct values MUST be returned without further constraint

### Requirement: Sorted Return Values

The system MUST return distinct values sorted alphabetically for string columns and numerically for integer/numeric columns. NULL values MUST be excluded from the returned lists.

#### Scenario: Alphabetical sort for generico

- GIVEN `dim_articulo` contains generico values `['VINOS', 'CERVEZAS', 'AGUAS']`
- WHEN a client sends `GET /api/filter-values/dim_articulo`
- THEN `generico` values in the response MUST be `['AGUAS', 'CERVEZAS', 'VINOS']`

#### Scenario: NULL values excluded

- GIVEN a filterable column contains some NULL rows
- WHEN the endpoint is called
- THEN NULL values MUST NOT appear in the returned list for that column

### Requirement: Parameterized Queries Only

The system MUST use psycopg2 `%s` parameterized queries for all cascade constraint values. The system MUST NOT use f-string interpolation for any user-supplied value.

#### Scenario: SQL injection attempt in query param

- GIVEN a client sends `GET /api/filter-values/dim_articulo?generico='; DROP TABLE gold.dim_articulo; --`
- WHEN the endpoint processes the request
- THEN the query MUST execute safely without modifying data
- AND the response MUST return an empty list or `400` if the value doesn't match the allowlist type
