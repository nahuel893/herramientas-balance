import pandas as pd

from . import repository

FACT_TABLES = {"fact_ventas", "fact_ventas_contabilidad", "fact_stock"}
ARTICULO_COLUMNS = {"generico", "marca"}


def discard_unique_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    discarded = []
    for col in df.columns.tolist():
        if df[col].nunique() <= 1:
            discarded.append(col)
    df = df.drop(columns=discarded)
    return df, discarded


def write_csv(df: pd.DataFrame, output_path: str) -> None:
    df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')


def _build_conditions(
    table: str,
    filters: list | None,
    date_column: str | None,
    date_from: str | None,
    date_to: str | None,
) -> list[tuple[str, list]]:
    """Build parameterized conditions as (fragment, values) tuples."""
    conditions: list[tuple[str, list]] = []

    # Date filters — parameterized, no f-string interpolation of values
    if date_column and date_from:
        conditions.append((f'"{date_column}" >= %s', [date_from]))
    if date_column and date_to:
        conditions.append((f'"{date_column}" <= %s', [date_to]))

    # Column filters
    for f in (filters or []):
        col = f.column if hasattr(f, 'column') else f['column']
        vals = f.values if hasattr(f, 'values') else f['values']
        if not vals:
            continue
        placeholders = ', '.join(['%s'] * len(vals))
        if table in FACT_TABLES and col in ARTICULO_COLUMNS:
            # generico/marca live in dim_articulo, not in the fact table directly
            conditions.append((
                f'"id_articulo" IN (SELECT "id_articulo" FROM gold."dim_articulo" WHERE "{col}" IN ({placeholders}))',
                list(vals),
            ))
        else:
            conditions.append((f'"{col}" IN ({placeholders})', list(vals)))

    return conditions


def run_preview(
    table: str,
    columns: list[str],
    filters: list | None = None,
    date_column: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    conditions = _build_conditions(table, filters, date_column, date_from, date_to)
    df = repository.fetch_data(table, columns, conditions)
    df = df.head(100)
    return {
        "columns": df.columns.tolist(),
        "data": df.values.tolist(),
        "count": len(df),
    }


def run_export(
    table: str,
    columns: list[str],
    output_path: str,
    date_column: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    filters: list | None = None,
) -> tuple[int, list[str], list[str]]:
    conditions = _build_conditions(table, filters, date_column, date_from, date_to)
    df = repository.fetch_data(table, columns, conditions)
    df, discarded = discard_unique_columns(df)
    write_csv(df, output_path)

    return len(df), df.columns.tolist(), discarded
