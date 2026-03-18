# Services Specification

## Purpose

Business logic layer. Contains pure functions (no I/O) and use-case orchestrators. MUST NOT import psycopg2 or write to the database directly. All pure functions MUST be testable without a database connection.

## Requirements

### Requirement: build_select_query (pure)

The module MUST expose `build_select_query(table: str, columns: list[str], date_column: str | None, date_from: str | None, date_to: str | None) -> str` that builds and returns a SQL SELECT string.

This function MUST be pure — it has no side effects and returns the same output for the same inputs. Column names MUST be escaped with double quotes.

#### Scenario: Query with no date filter

- GIVEN table `"ventas"`, columns `["id", "monto"]`, all date args `None`
- WHEN `build_select_query(...)` is called
- THEN it returns `'SELECT "id", "monto" FROM silver."ventas"'`
- AND no WHERE clause is present

#### Scenario: Query with both date bounds

- GIVEN `date_column="fecha"`, `date_from="2024-01-01"`, `date_to="2024-12-31"`
- WHEN `build_select_query(...)` is called
- THEN the result contains `WHERE "fecha" >= '2024-01-01' AND "fecha" <= '2024-12-31'`

#### Scenario: Query with only date_from

- GIVEN `date_column="fecha"`, `date_from="2024-01-01"`, `date_to=None`
- WHEN `build_select_query(...)` is called
- THEN the result contains only the `>=` condition, no `<=` condition

#### Scenario: date_to provided but date_column is None

- GIVEN `date_column=None`, `date_from=None`, `date_to="2024-12-31"`
- WHEN `build_select_query(...)` is called
- THEN no WHERE clause is added (date filter requires `date_column`)

---

### Requirement: discard_unique_columns (pure)

The module MUST expose `discard_unique_columns(df: DataFrame) -> tuple[DataFrame, list[str]]` that removes columns with a single unique value from the DataFrame.

This function MUST be pure — it does not read from disk or network.

#### Scenario: Some columns have a single unique value

- GIVEN a DataFrame where column `"estado"` has only one distinct value
- WHEN `discard_unique_columns(df)` is called
- THEN the returned DataFrame does NOT contain `"estado"`
- AND the returned list contains `"estado"`

#### Scenario: All columns have multiple unique values

- GIVEN a DataFrame where every column has >= 2 distinct values
- WHEN `discard_unique_columns(df)` is called
- THEN the returned DataFrame is identical to the input
- AND the returned list is empty `[]`

#### Scenario: Empty DataFrame

- GIVEN a DataFrame with zero rows
- WHEN `discard_unique_columns(df)` is called
- THEN all columns are considered unique-value columns (nunique == 0 <= 1)
- AND they are all discarded

---

### Requirement: run_preview

The module MUST expose `run_preview(table: str, columns: list[str]) -> dict` that fetches up to 100 rows and returns a dict with keys `columns` (list), `data` (list of lists), `count` (int).

`run_preview` MAY delegate to `repository.fetch_data` with an empty conditions list.

#### Scenario: Preview returns data

- GIVEN a valid table and non-empty columns list
- WHEN `run_preview("ventas", ["id", "monto"])` is called
- THEN the result dict has keys `columns`, `data`, `count`
- AND `count` equals `len(data)`
- AND `count` is at most 100

---

### Requirement: run_export

The module MUST expose `run_export(table: str, columns: list[str], output_path: str, date_column: str | None, date_from: str | None, date_to: str | None) -> tuple[int, list[str], list[str]]` returning `(row_count, exported_columns, discarded_columns)`.

`run_export` MUST apply `discard_unique_columns` before writing the CSV. The CSV MUST be written with `sep=';'` and `encoding='utf-8-sig'`, without the index column.

#### Scenario: Export with discarded columns

- GIVEN a table where column `"pais"` has a single unique value
- WHEN `run_export(...)` is called
- THEN the written CSV does NOT contain `"pais"`
- AND the returned `discarded_columns` list contains `"pais"`
- AND `exported_columns` contains the remaining columns

#### Scenario: Export with date filter

- GIVEN `date_from="2024-01-01"` and `date_to="2024-03-31"`
- WHEN `run_export(...)` is called
- THEN only rows within the date range are written to the CSV

#### Scenario: No columns discarded

- GIVEN all requested columns have >= 2 distinct values
- WHEN `run_export(...)` is called
- THEN `discarded_columns` is `[]`
- AND `exported_columns` equals the originally requested columns
