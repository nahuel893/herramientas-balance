# repository Specification

## Delta for repository

## ADDED Requirements

### Requirement: get_column_values Function

The system MUST add a function `get_column_values(table: str, column: str, parent_filters: list[ColumnFilter]) -> list` to `app/repository.py`. It MUST return a sorted list of distinct non-NULL values for the specified column, optionally constrained by `parent_filters`.

#### Scenario: Distinct values with no parent filters

- GIVEN `table="dim_articulo"`, `column="generico"`, `parent_filters=[]`
- WHEN `get_column_values()` is called
- THEN it MUST execute `SELECT DISTINCT "generico" FROM gold."dim_articulo" WHERE "generico" IS NOT NULL ORDER BY "generico"`
- AND MUST return a list of strings sorted alphabetically

#### Scenario: Distinct values with cascade parent filter

- GIVEN `table="dim_articulo"`, `column="marca"`, `parent_filters=[ColumnFilter(column="generico", values=["CERVEZAS"])]`
- WHEN `get_column_values()` is called
- THEN the query MUST include `WHERE "generico" IN %s AND "marca" IS NOT NULL`
- AND the params MUST include `("CERVEZAS",)` as the parameterized value
- AND the returned list MUST contain only marcas that exist for CERVEZAS

#### Scenario: All values use parameterized queries

- GIVEN any `parent_filters` value
- WHEN `get_column_values()` builds its SQL query
- THEN every filter value MUST appear in the params list passed to psycopg2
- AND MUST NOT be interpolated into the query string via f-strings

## MODIFIED Requirements

### Requirement: fetch_data Accepts params Alongside conditions

The system MUST update `fetch_data()` to support parameterized query values. The signature MUST change to accept a `params` list (or equivalent mechanism) so that `pd.read_sql(query, conn, params=params)` can be called with the values separated from the query string.

(Previously: `fetch_data(table_name, columns, conditions)` accepted pre-built condition strings with no separate params — conditions were concatenated directly into the query and passed without params.)

#### Scenario: fetch_data executes with parameterized conditions

- GIVEN `conditions=["\"generico\" IN %s"]` and `params=[("CERVEZAS", "VINOS")]`
- WHEN `fetch_data()` is called
- THEN it MUST call `pd.read_sql(query, conn, params=params)`
- AND the final SQL MUST NOT contain literal filter values in the query string

#### Scenario: fetch_data with empty conditions (backward compat)

- GIVEN `conditions=[]` and `params=[]`
- WHEN `fetch_data()` is called
- THEN it MUST return all rows from the table without a WHERE clause
- AND MUST NOT raise an error

#### Scenario: Column names remain double-quoted

- GIVEN any call to `fetch_data()`
- WHEN the query is built
- THEN each selected column MUST be wrapped in double quotes (e.g., `"col_name"`)
- AND the table name MUST be schema-qualified as `gold."table_name"`
