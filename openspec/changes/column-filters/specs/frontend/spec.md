# frontend Specification

## Delta for frontend

## ADDED Requirements

### Requirement: Static Filter Config in app.js

The system MUST define a static configuration object in `app/static/app.js` that maps each filterable table to its ordered list of filterable columns. This config MUST mirror the server-side allowlist.

```
TABLE_FILTER_CONFIG = {
  dim_articulo: ["generico", "marca"],
  fact_ventas: ["id_sucursal", "generico", "marca"],
  fact_ventas_contabilidad: ["id_sucursal", "generico", "marca"],
  fact_stock: ["id_deposito", "generico", "marca"],
  dim_cliente: ["id_sucursal"]
}
```

#### Scenario: Config present at page load

- GIVEN the page loads
- WHEN `app.js` is evaluated
- THEN `TABLE_FILTER_CONFIG` MUST be defined before any table-selection event fires

### Requirement: Filter Section Renders Dynamically on Table Select

The system MUST render filter controls in `index.html` based on the selected table. For each column in `TABLE_FILTER_CONFIG[selectedTable]`, a `<select>` dropdown MUST be rendered. When the selected table has no entry in the config, the filter section MUST be hidden.

#### Scenario: Table with filterable columns selected

- GIVEN a user selects `dim_articulo` from the table list
- WHEN the table-select event fires
- THEN the filter section MUST become visible
- AND MUST render two dropdowns: one for `generico`, one for `marca`
- AND each dropdown MUST be populated by calling `GET /api/filter-values/dim_articulo`

#### Scenario: Table with no filterable columns selected

- GIVEN a user selects a table not present in `TABLE_FILTER_CONFIG`
- WHEN the table-select event fires
- THEN the filter section MUST be hidden or empty
- AND no `/api/filter-values` request MUST be made

#### Scenario: Table changes while filters are active

- GIVEN a user has selected filters for `fact_ventas`
- WHEN the user selects a different table
- THEN all previously selected filter values MUST be cleared
- AND the filter section MUST re-render for the new table

### Requirement: Cascade — generico Change Refreshes marca

When a table's filter config includes both `generico` and `marca`, changing the `generico` dropdown MUST trigger a fetch to reload `marca` values filtered by the selected `generico`.

#### Scenario: generico selection triggers marca reload

- GIVEN `dim_articulo` is selected and both dropdowns are rendered
- WHEN the user selects `generico = "CERVEZAS"`
- THEN the frontend MUST call `GET /api/filter-values/dim_articulo?generico=CERVEZAS`
- AND MUST replace the `marca` dropdown options with the returned values
- AND the previously selected `marca` value MUST be cleared

#### Scenario: generico cleared resets marca to all values

- GIVEN a user has selected `generico = "CERVEZAS"` and then clears the selection
- WHEN the generico dropdown returns to the empty/all state
- THEN the frontend MUST call `GET /api/filter-values/dim_articulo` (no params)
- AND MUST repopulate `marca` with all available values

### Requirement: Filters Included in Preview and Export POST Bodies

The system MUST include the currently selected filters in the JSON body of both `POST /api/preview` and `POST /api/export` requests. Filters with no selected value (empty or "all") MUST NOT be included in the request body.

#### Scenario: Preview with active filter

- GIVEN `generico = "CERVEZAS"` is selected for `dim_articulo`
- WHEN the user clicks Preview
- THEN the POST body MUST contain `"filters": [{"column": "generico", "values": ["CERVEZAS"]}]`

#### Scenario: Preview with no filters selected

- GIVEN no filter dropdowns have a selected value
- WHEN the user clicks Preview
- THEN the POST body MUST either omit `filters` or send `"filters": null`
- AND MUST NOT send `"filters": []` with empty `values` arrays

#### Scenario: Export includes same filters as preview

- GIVEN the same filter state that was used for preview
- WHEN the user clicks Export
- THEN the POST body for export MUST include the identical `filters` array

## MODIFIED Requirements

### Requirement: index.html Contains Filter Section Placeholder

The system MUST add a filter section container to `app/templates/index.html`. This container MUST be initially hidden and MUST have an `id` attribute that `app.js` uses to inject filter controls.

(Previously: `index.html` had no filter section — only date filter inputs.)

#### Scenario: Filter section present in DOM

- GIVEN the page loads
- WHEN the DOM is inspected
- THEN a filter container element MUST exist
- AND it MUST be hidden by default (e.g., `class="hidden"` with Tailwind)
