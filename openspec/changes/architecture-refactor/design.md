# Design: Architecture Refactor — Clean Layer Separation

## Technical Approach

Split `app/database.py` (77 lines, 5 responsibilities) and inline helpers in `main.py` into 3 dedicated modules following Single Responsibility Principle. No behavior changes — pure structural reorganization. The refactor is safe-by-construction: new modules are created first, imports are updated last, `database.py` is deleted only after everything works.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| `build_select_query` as pure function | Yes — takes params, returns SQL string, no I/O | Keep embedded in `fetch_data` | Pure = testable without DB mock. The SQL string can be asserted directly. |
| `discard_unique_columns` as pure function | Yes — takes DataFrame, returns (DataFrame, list[str]) | Keep embedded in `export_data` | Same rationale: testable with a fixture DataFrame, no DB needed. |
| `storage.py` separate from `services.py` | Yes — filesystem I/O is infrastructure, not business logic | Single `services.py` for everything | `services.py` should have zero `os`/`json` imports. Storage concern is orthogonal to export/preview logic. |
| Delete `database.py`, no shim | Yes — deleted at end of migration | Keep as re-export shim | A shim would leave a dead file that misleads future readers. The migration order makes the delete safe. |
| Dependency direction: main → services → repository | Unidirectional, no circulars | Any other direction | `repository.py` has zero knowledge of business rules. `services.py` has zero knowledge of HTTP. `main.py` is the only layer that knows about FastAPI. |
| `storage.py` imported only by `main.py` | Yes — main calls storage directly | Services call storage | Storage is infrastructure triggered by HTTP handlers, not an internal step of business logic. |

## Module Structure

```
app/
├── main.py        # FastAPI routes — HTTP in/out only
├── repository.py  # psycopg2 + SQL — data access layer
├── services.py    # Business logic — pure functions + use cases
└── storage.py     # selections.json CRUD — local persistence
```

### Public Interfaces

**`repository.py`**
```python
def get_connection() -> psycopg2.connection
def get_silver_tables() -> list[str]
def get_table_columns(table_name: str) -> list[dict]
def fetch_data(table_name: str, columns: list[str], conditions: list[str]) -> pd.DataFrame
```

**`services.py`**
```python
# Pure functions (no I/O, fully testable)
def build_select_query(table: str, columns: list[str], date_column: str | None, date_from: str | None, date_to: str | None) -> str
def discard_unique_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]

# Use cases (orchestrate repository calls)
def write_csv(df: pd.DataFrame, output_path: str) -> None
def run_preview(table: str, columns: list[str]) -> dict
def run_export(table: str, columns: list[str], output_path: str, date_column: str | None, date_from: str | None, date_to: str | None) -> dict
```

**`storage.py`**
```python
def load_selections() -> dict
def save_selection(name: str, table: str, columns: list[str]) -> None
def delete_selection(name: str) -> None
```

## Dependency Diagram

```
main.py
  ├──→ services.py ──→ repository.py ──→ PostgreSQL
  └──→ storage.py  ──→ selections.json
```

No arrows point upward or sideways between `services.py`, `storage.py`, and `repository.py`.

## Data Flow — POST /api/export

```
HTTP POST /api/export (ExportRequest)
  │
  ▼
main.py: api_export()
  │  builds filename + filepath (timestamp logic stays in main)
  │
  ▼
services.run_export(table, columns, filepath, date_column, date_from, date_to)
  │
  ├──→ services.build_select_query(...)  ──→ returns SQL string (pure)
  │
  ├──→ repository.fetch_data(table, columns, conditions)
  │     └──→ repository.get_connection() → psycopg2 connect
  │     └──→ pd.read_sql(query, conn)    → DataFrame
  │
  ├──→ services.discard_unique_columns(df)  ──→ (clean_df, discarded) (pure)
  │
  └──→ services.write_csv(clean_df, filepath)
        └──→ df.to_csv(sep=';', encoding='utf-8-sig')

  ▼
main.py: returns JSON {filename, count, exported_columns, discarded_columns}
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/repository.py` | Create | `get_connection`, `get_silver_tables`, `get_table_columns`, `fetch_data` |
| `app/services.py` | Create | `build_select_query` (pure), `discard_unique_columns` (pure), `write_csv`, `run_preview`, `run_export` |
| `app/storage.py` | Create | `load_selections`, `save_selection`, `delete_selection` — extracted from `main.py` |
| `app/main.py` | Modify | Remove `load_selections`/`save_selections` helpers, update import from `.database` to new modules |
| `app/database.py` | Delete | Replaced entirely by `repository.py` + logic moved to `services.py` |

## Migration Order

Safe sequence — app stays runnable at every step:

1. **Create `repository.py`** — extract `get_connection`, `get_silver_tables`, `get_table_columns` verbatim. `fetch_data` receives a pre-built SQL string (from services) and executes it.
2. **Create `services.py`** — extract `build_select_query` and `discard_unique_columns` as pure functions. `run_preview` and `run_export` call `repository.fetch_data` internally.
3. **Create `storage.py`** — extract `load_selections`/`save_selections` verbatim from `main.py`. Rename `save_selections` → `save_selection` (single-entry semantics).
4. **Update `main.py`** — replace `from .database import ...` with imports from the three new modules. Remove inline helper functions. Verify app starts.
5. **Delete `app/database.py`** — only after step 4 is confirmed working.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `build_select_query` — SQL string output for all date filter combinations | Call with params, assert returned string (no DB) |
| Unit | `discard_unique_columns` — correct discard of constant columns | Pass fixture DataFrame, assert returned columns |
| Integration | `run_preview`, `run_export` — end-to-end with real DB | Manual call via `/api/preview` and `/api/export` endpoints |
| Integration | `storage.py` CRUD — file read/write | Call `save_selection`, then `load_selections`, assert key present |

Note: Test implementation is out of scope for this change (tracked as `implement-testing`).

## Open Questions

- None — design is fully determined by the current codebase structure and proposal constraints.
