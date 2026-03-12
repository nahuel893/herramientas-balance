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

def get_silver_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'silver'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables

def get_table_columns(table_name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'silver' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in cur.fetchall()]
    conn.close()
    return columns

def preview_data(table_name: str, columns: list, limit: int = 100):
    conn = get_connection()
    safe_columns = ', '.join([f'"{col}"' for col in columns])
    query = f'SELECT {safe_columns} FROM silver."{table_name}" LIMIT {limit}'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def export_data(table_name: str, columns: list, output_path: str, date_column: str = None, date_from: str = None, date_to: str = None):
    conn = get_connection()
    safe_columns = ', '.join([f'"{col}"' for col in columns])
    query = f'SELECT {safe_columns} FROM silver."{table_name}"'

    conditions = []
    if date_column and date_from:
        conditions.append(f'"{date_column}" >= \'{date_from}\'')
    if date_column and date_to:
        conditions.append(f'"{date_column}" <= \'{date_to}\'')

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    df = pd.read_sql(query, conn)
    conn.close()

    # Revisar columnas con 1 solo valor unico y descartarlas
    discarded = []
    for col in df.columns.tolist():
        if df[col].nunique() <= 1:
            discarded.append(col)
    df = df.drop(columns=discarded)

    df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
    return len(df), df.columns.tolist(), discarded
