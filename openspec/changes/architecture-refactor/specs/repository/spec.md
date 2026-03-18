# Repository Specification

## Purpose

Data access layer. Responsible for all interactions with PostgreSQL. MUST NOT contain business logic, CSV writing, or column filtering. Replaces `app/database.py`.

## Requirements

### Requirement: get_silver_tables

The module MUST expose `get_silver_tables() -> list[str]` that returns table names from `information_schema` filtered by `table_schema = 'silver'`, ordered by `table_name`.

#### Scenario: Tables exist in silver schema

- GIVEN a live PostgreSQL connection to `medallion_db`
- WHEN `get_silver_tables()` is called
- THEN it returns a list of strings (table names), sorted alphabetically
- AND the connection is closed before returning

#### Scenario: No tables in silver schema

- GIVEN the silver schema has no tables
- WHEN `get_silver_tables()` is called
- THEN it returns an empty list `[]`

---

### Requirement: get_table_columns

The module MUST expose `get_table_columns(table_name: str) -> list[dict]` that returns column metadata for a given table in the silver schema.

Each dict MUST contain keys: `name` (str), `type` (str), `nullable` (str).

#### Scenario: Columns retrieved for a valid table

- GIVEN a table name that exists in `silver` schema
- WHEN `get_table_columns("some_table")` is called
- THEN it returns a list of dicts with `name`, `type`, `nullable`
- AND columns are ordered by `ordinal_position`
- AND the connection is closed before returning

#### Scenario: Table does not exist

- GIVEN a table name not present in `silver` schema
- WHEN `get_table_columns("nonexistent")` is called
- THEN it returns an empty list `[]`

---

### Requirement: fetch_data

The module MUST expose `fetch_data(table_name: str, columns: list[str], conditions: list[str]) -> DataFrame` that executes a SELECT and returns a pandas DataFrame.

`fetch_data` MUST NOT apply any column filtering, uniqueness checks, or transformations — it returns raw data only.

Column names MUST be escaped with double quotes in the SQL query.

#### Scenario: Fetch with no conditions

- GIVEN a valid table and non-empty columns list
- WHEN `fetch_data("t", ["col_a", "col_b"], [])` is called
- THEN it returns a DataFrame with exactly those columns
- AND no WHERE clause is added to the SQL

#### Scenario: Fetch with date conditions

- GIVEN a valid table, columns, and a non-empty conditions list
- WHEN `fetch_data("t", ["col_a"], ['"date_col" >= \'2024-01-01\''])` is called
- THEN the SQL includes a WHERE clause with all conditions joined by `AND`
- AND the returned DataFrame contains only rows matching the condition

#### Scenario: Empty columns list

- GIVEN an empty columns list
- WHEN `fetch_data("t", [], [])` is called
- THEN behavior is unspecified — callers MUST NOT pass an empty columns list

---

### Requirement: Connection management

Each function MUST open a new psycopg2 connection using environment variables (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) and MUST close it before returning, even if an exception occurs.
