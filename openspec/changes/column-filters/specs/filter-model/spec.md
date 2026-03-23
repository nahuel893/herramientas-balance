# filter-model Specification

## Purpose

New Pydantic model `ColumnFilter` and modifications to `PreviewRequest` and `ExportRequest` to carry dimension filter lists.

## Requirements

### Requirement: ColumnFilter Model

The system MUST define a Pydantic model `ColumnFilter` in `app/main.py` with the following fields:

| Field | Type | Constraint |
|-------|------|-----------|
| `column` | `str` | MUST be non-empty |
| `values` | `list[str]` | MUST contain at least one element when present |

The `column` field MUST be validated against the server-side filterable columns allowlist at the service or endpoint layer — Pydantic alone is not sufficient to enforce business rules.

#### Scenario: Valid ColumnFilter

- GIVEN a POST body contains `{"column": "generico", "values": ["CERVEZAS"]}`
- WHEN Pydantic parses it as `ColumnFilter`
- THEN the model MUST instantiate without error

#### Scenario: Empty values list

- GIVEN a POST body contains `{"column": "generico", "values": []}`
- WHEN this filter is included in a request
- THEN the system SHOULD treat it as no filter applied for that column (equivalent to omitting the filter)

### Requirement: PreviewRequest Gains filters Field

The system MUST add `filters: Optional[list[ColumnFilter]] = None` to `PreviewRequest`. Existing fields (`table`, `columns`) MUST remain unchanged.

#### Scenario: Preview with no filters (backward compatibility)

- GIVEN an existing client sends `POST /api/preview` without a `filters` key
- WHEN the request is parsed
- THEN `filters` MUST default to `None` and the request MUST succeed

#### Scenario: Preview with filters

- GIVEN a client sends `POST /api/preview` with `filters: [{"column": "generico", "values": ["CERVEZAS"]}]`
- WHEN the request is parsed
- THEN `req.filters` MUST contain one `ColumnFilter` with `column="generico"` and `values=["CERVEZAS"]`

### Requirement: ExportRequest Gains filters Field

The system MUST add `filters: Optional[list[ColumnFilter]] = None` to `ExportRequest`. Existing fields (`table`, `columns`, `date_column`, `date_from`, `date_to`) MUST remain unchanged.

#### Scenario: Export with filters and date range

- GIVEN a client sends `POST /api/export` with both `filters` and `date_from`/`date_to`
- WHEN the request is parsed
- THEN both `filters` and date fields MUST be accessible on the request object
- AND both filter types MUST be applied when the export runs
