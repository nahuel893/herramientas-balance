# Delta for services

## MODIFIED Requirements

### Requirement: Query Builder Uses Gold Schema

`build_select_query()` MUST generate a FROM clause referencing `gold."{table}"`. It MUST NOT generate `silver."{table}"`.

#### Scenario: Query built for gold table

- GIVEN a valid table name and a non-empty columns list
- WHEN `build_select_query(table, columns, ...)` is called
- THEN the returned SQL string contains `FROM gold."{table}"`
- AND column identifiers are escaped with double quotes

#### Scenario: Query built with date range filter

- GIVEN a table name, columns, a date column, and both `date_from` and `date_to` values
- WHEN `build_select_query(table, columns, date_column, date_from, date_to)` is called
- THEN the returned SQL contains `FROM gold."{table}"`
- AND the WHERE clause includes both date boundary conditions

#### Scenario: Query built with only date_from

- GIVEN only `date_from` is provided (no `date_to`)
- WHEN `build_select_query(table, columns, date_column, date_from, None)` is called
- THEN only the lower-bound condition appears in WHERE
- AND the FROM clause uses `gold."{table}"`
