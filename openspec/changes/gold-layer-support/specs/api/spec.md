# Delta for api

## MODIFIED Requirements

### Requirement: `/api/tables` Returns Gold Tables Only

The `/api/tables` endpoint MUST call `repository.get_tables()` (not `get_silver_tables()`). It MUST return only tables from the `gold` schema. It MUST NOT accept or expose a `schema` query parameter.

#### Scenario: Tables listed from gold schema

- GIVEN the application is running and the DB is reachable
- WHEN a GET request is made to `/api/tables`
- THEN the response JSON contains a `tables` array with gold schema table names only
- AND no silver or bronze table names appear in the response

#### Scenario: DB unreachable

- GIVEN the DB is not reachable
- WHEN a GET request is made to `/api/tables`
- THEN the endpoint returns an HTTP error response (5xx)

---

### Requirement: `/api/columns/{table_name}` Resolves Against Gold Schema

The `/api/columns/{table_name}` endpoint MUST return columns from the `gold` schema for the given table. Callers MUST NOT pass a schema parameter — the schema is fixed.

#### Scenario: Columns returned for valid gold table

- GIVEN `table_name` exists in the `gold` schema
- WHEN a GET request is made to `/api/columns/{table_name}`
- THEN the response JSON contains a `columns` array with `name`, `type`, and `nullable` fields

#### Scenario: Table not in gold schema

- GIVEN `table_name` does not exist in `gold`
- WHEN a GET request is made to `/api/columns/{table_name}`
- THEN the response JSON contains an empty `columns` array

---

### Requirement: Preview and Export Operate on Gold Tables

`/api/preview` and `/api/export` MUST call service and repository functions that query the `gold` schema. They MUST NOT pass a schema parameter — the schema is implicit.

#### Scenario: Preview fetches gold data

- GIVEN a valid gold table name and a column list
- WHEN a POST request is made to `/api/preview` with `{table, columns}`
- THEN the response returns up to 100 rows from `gold."{table}"`

#### Scenario: Export writes gold data to CSV

- GIVEN a valid gold table, columns, and optional date filters
- WHEN a POST request is made to `/api/export`
- THEN a CSV file is generated from `gold."{table}"` data
- AND the response includes `filename`, `count`, `exported_columns`, and `discarded_columns`

## REMOVED Requirements

### Requirement: App Title References Silver

(Reason: The FastAPI app title SHOULD be updated from `"Silver Column Selector"` to `"Gold Column Selector"` to reflect the migrated schema. This is a cosmetic change but prevents user confusion.)
