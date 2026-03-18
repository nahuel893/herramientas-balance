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


def fetch_data(table_name: str, columns: list[str], conditions: list[str]) -> pd.DataFrame:
    conn = get_connection()
    safe_columns = ', '.join([f'"{col}"' for col in columns])
    query = f'SELECT {safe_columns} FROM gold."{table_name}"'
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    df = pd.read_sql(query, conn)
    conn.close()
    return df
