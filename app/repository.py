import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )


def get_tables() -> list[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'gold'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables


def get_table_columns(table_name: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'gold' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in cur.fetchall()]
    conn.close()
    return columns


def fetch_data(table_name: str, columns: list[str], conditions: list[tuple[str, list]]) -> pd.DataFrame:
    conn = get_connection()
    safe_columns = ', '.join([f'"{col}"' for col in columns])
    query = f'SELECT {safe_columns} FROM gold."{table_name}"'
    params = [v for _, vals in conditions for v in vals]
    if conditions:
        query += ' WHERE ' + ' AND '.join([fragment for fragment, _ in conditions])
    df = pd.read_sql(query, conn, params=params or None)
    conn.close()
    return df


def get_column_values(table: str, column: str, parent_filters: dict) -> list:
    """Return sorted distinct non-NULL values for `column` in `table`,
    optionally constrained by `parent_filters` ({col: [val, ...]}).

    For generico/marca on fact tables, queries dim_articulo directly.
    """
    ARTICULO_COLUMNS = {"generico", "marca"}
    FACT_TABLES = {"fact_ventas", "fact_ventas_contabilidad", "fact_stock"}

    # Determine which table to actually query
    if column in ARTICULO_COLUMNS and table in FACT_TABLES:
        target_table = "dim_articulo"
    else:
        target_table = table

    conn = get_connection()
    cur = conn.cursor()

    conditions = []
    params = []
    for filter_col, filter_vals in (parent_filters or {}).items():
        if not filter_vals:
            continue
        placeholders = ', '.join(['%s'] * len(filter_vals))
        conditions.append(f'"{filter_col}" IN ({placeholders})')
        params.extend(filter_vals)

    query = f'SELECT DISTINCT "{column}" FROM gold."{target_table}"'
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += f' ORDER BY "{column}"'

    cur.execute(query, params)
    values = [row[0] for row in cur.fetchall() if row[0] is not None]
    conn.close()
    return values
