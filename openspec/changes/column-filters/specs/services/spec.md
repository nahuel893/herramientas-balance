# services Specification

## Delta for services

## MODIFIED Requirements

### Requirement: build_select_query Accepts and Applies ColumnFilter List

The system MUST update `build_select_query()` to accept a `filters: list[ColumnFilter]` parameter. For each filter, it MUST generate an `IN` clause using psycopg2 `%s` parameterized form. The function MUST return both the query string and the params list.

(Previously: `build_select_query()` returned only a query string with no filter support and used f-string interpolation for date conditions.)

#### Scenario: Single column filter applied

- GIVEN `filters = [ColumnFilter(column="generico", values=["CERVEZAS", "VINOS"])]`
- WHEN `build_select_query()` is called
- THEN the returned query MUST contain `"generico" IN %s` (or equivalent `%s, %s` form)
- AND the returned params MUST include the tuple `("CERVEZAS", "VINOS")` for that placeholder

#### Scenario: Multiple column filters combined

- GIVEN `filters` contains two `ColumnFilter` entries for `generico` and `id_sucursal`
- WHEN `build_select_query()` is called
- THEN the WHERE clause MUST include both conditions joined with `AND`
- AND the params list MUST include values for both filters in matching order

#### Scenario: No column filters

- GIVEN `filters = []` or `filters = None`
- WHEN `build_select_query()` is called
- THEN no additional WHERE conditions MUST be added for column filters
- AND the function MUST behave identically to the previous implementation (modulo the SQL injection fix)

### Requirement: Date Filter Conditions Use Parameterized Form

The system MUST remove all f-string interpolation of `date_from` and `date_to` values. Date conditions MUST be emitted as `"col" >= %s` and `"col" <= %s` with values passed as params.

(Previously: `conditions.append(f'"{date_column}" >= \'{date_from}\'')`  — SQL injection vector.)

#### Scenario: Date range applied safely

- GIVEN `date_column="fecha"`, `date_from="2024-01-01"`, `date_to="2024-12-31"`
- WHEN `build_select_query()` is called
- THEN the query MUST contain `"fecha" >= %s AND "fecha" <= %s` (no literal values in the string)
- AND the params list MUST contain `"2024-01-01"` and `"2024-12-31"` as separate elements

#### Scenario: Injection attempt in date_from

- GIVEN `date_from = "'; DROP TABLE gold.fact_ventas; --"`
- WHEN `build_select_query()` is called
- THEN the value MUST appear only in the params list, never interpolated into the query string

### Requirement: run_preview Passes Filters to fetch_data

The system MUST update `run_preview()` to accept `filters: list[ColumnFilter]` and pass them to the data fetch layer. The hardcoded `[]` for conditions MUST be replaced.

(Previously: `run_preview()` called `repository.fetch_data(table, columns, [])` — ignoring all conditions.)

#### Scenario: Preview with active filters returns filtered rows

- GIVEN the table contains rows where `generico` is both `CERVEZAS` and `VINOS`
- WHEN `run_preview()` is called with `filters=[ColumnFilter(column="generico", values=["CERVEZAS"])]`
- THEN the returned DataFrame MUST contain only rows where `generico = 'CERVEZAS'`
- AND the count MUST be less than or equal to 100

#### Scenario: Preview with no filters returns unfiltered rows (backward compat)

- GIVEN `filters=None` or `filters=[]`
- WHEN `run_preview()` is called
- THEN behavior MUST be identical to the previous implementation

### Requirement: run_export Passes Filters to fetch_data

The system MUST update `run_export()` to accept `filters: list[ColumnFilter]` and apply them when fetching data. The discarded-columns logic MUST still run on the filtered dataset.

#### Scenario: Export with filters applies filters before discard-columns

- GIVEN filters reduce the dataset to rows where `generico = 'CERVEZAS'`
- WHEN `run_export()` is called
- THEN the CSV MUST contain only filtered rows
- AND `discard_unique_columns()` MUST operate on the already-filtered DataFrame

## ADDED Requirements

### Requirement: No f-string Interpolation of User-Controlled Values

The system MUST NOT use f-string interpolation for any value that originates from user input anywhere in `services.py`. Column names that come from the server-side selected columns list MAY continue to use double-quoted f-string formatting (e.g., `f'"{col}"'`) as they are controlled by the application schema, not arbitrary user input.

#### Scenario: Audit — all user values go through params

- GIVEN a code review of `services.py`
- WHEN checking all WHERE clause generation
- THEN every user-supplied filter value MUST appear only as `%s` in the query string
- AND MUST be present in the corresponding params list passed to the database layer
