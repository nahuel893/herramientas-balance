import pandas as pd

from . import repository


def build_select_query(
    table: str,
    columns: list[str],
    date_column: str | None,
    date_from: str | None,
    date_to: str | None,
) -> str:
    safe_columns = ', '.join([f'"{col}"' for col in columns])
    query = f'SELECT {safe_columns} FROM gold."{table}"'

    conditions = []
    if date_column and date_from:
        conditions.append(f'"{date_column}" >= \'{date_from}\'')
    if date_column and date_to:
        conditions.append(f'"{date_column}" <= \'{date_to}\'')

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    return query


def discard_unique_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    discarded = []
    for col in df.columns.tolist():
        if df[col].nunique() <= 1:
            discarded.append(col)
    df = df.drop(columns=discarded)
    return df, discarded


def write_csv(df: pd.DataFrame, output_path: str) -> None:
    df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')


def run_preview(table: str, columns: list[str]) -> dict:
    df = repository.fetch_data(table, columns, [])
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
) -> tuple[int, list[str], list[str]]:
    conditions = []
    if date_column and date_from:
        conditions.append(f'"{date_column}" >= \'{date_from}\'')
    if date_column and date_to:
        conditions.append(f'"{date_column}" <= \'{date_to}\'')

    df = repository.fetch_data(table, columns, conditions)
    df, discarded = discard_unique_columns(df)
    write_csv(df, output_path)

    return len(df), df.columns.tolist(), discarded
