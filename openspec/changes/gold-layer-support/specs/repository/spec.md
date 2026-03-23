# Delta for repository

## MODIFIED Requirements

### Requirement: Table Listing Targets Gold Schema

`get_tables()` (renamed from `get_silver_tables()`) MUST query `information_schema.tables` filtering by `table_schema = 'gold'`. It MUST NOT reference `silver` schema.

#### Scenario: List gold tables successfully

- GIVEN a working DB connection with access to `medallion_db`
- WHEN `get_tables()` is called
- THEN it returns only table names from the `gold` schema
- AND the list is ordered alphabetically by `table_name`

#### Scenario: No gold tables exist

- GIVEN the `gold` schema has no tables
- WHEN `get_tables()` is called
- THEN it returns an empty list without error

---

### Requirement: Column Introspection Targets Gold Schema

`get_table_columns(table_name)` MUST query `information_schema.columns` filtering by `table_schema = 'gold'`. It MUST NOT reference `silver` schema.

#### Scenario: Columns returned for valid gold table

- GIVEN a table name that exists in the `gold` schema
- WHEN `get_table_columns(table_name)` is called
- THEN it returns a list of dicts with `name`, `type`, and `nullable` fields
- AND columns are ordered by `ordinal_position`

#### Scenario: Table does not exist in gold schema

- GIVEN a table name that does not exist in `gold`
- WHEN `get_table_columns(table_name)` is called
- THEN it returns an empty list

---

### Requirement: Data Fetching Uses Gold Schema

`fetch_data(table_name, columns, conditions)` MUST construct a FROM clause using `gold."{table_name}"`. It MUST NOT use `silver."{table_name}"`.

#### Scenario: Data fetched from gold table

- GIVEN a valid gold table name and a non-empty columns list
- WHEN `fetch_data(table_name, columns, conditions)` is called
- THEN the generated SQL references `gold."{table_name}"` in the FROM clause
- AND column names are escaped with double quotes

#### Scenario: Data fetched with conditions

- GIVEN a valid gold table, columns list, and a non-empty conditions list
- WHEN `fetch_data(table_name, columns, conditions)` is called
- THEN the WHERE clause includes all provided conditions joined by AND
- AND the FROM clause still uses `gold."{table_name}"`

## REMOVED Requirements

### Requirement: Function Named `get_silver_tables`

(Reason: The function is renamed to `get_tables()` to match the gold schema migration. All callers in `main.py` MUST be updated accordingly.)
