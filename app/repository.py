import json
import sqlite3

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


# Columns that need description lookup from their dimension table
LABEL_LOOKUPS = {
    "id_sucursal": {"table": "dim_sucursal", "id_col": "id_sucursal", "desc_col": "descripcion"},
    "id_deposito": {"table": "dim_deposito", "id_col": "id_deposito", "desc_col": "descripcion"},
}


def _fetch_labels(column: str) -> dict:
    """Fetch id→description mapping from a dimension table for labeled columns."""
    lookup = LABEL_LOOKUPS.get(column)
    if not lookup:
        return {}
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f'SELECT "{lookup["id_col"]}", "{lookup["desc_col"]}" FROM gold."{lookup["table"]}" ORDER BY "{lookup["id_col"]}"'
    )
    labels = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return labels


def get_column_values(table: str, column: str, parent_filters: dict) -> list[dict]:
    """Return sorted distinct non-NULL values for `column` in `table`,
    optionally constrained by `parent_filters` ({col: [val, ...]}).

    Returns list of {"value": str, "label": str} dicts.
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
        # If querying a fact table but the filter column lives in dim_articulo,
        # use a subquery instead of a direct WHERE
        if target_table in FACT_TABLES and filter_col in ARTICULO_COLUMNS:
            conditions.append(
                f'"id_articulo" IN (SELECT "id_articulo" FROM gold."dim_articulo" WHERE "{filter_col}" IN ({placeholders}))'
            )
        else:
            conditions.append(f'"{filter_col}" IN ({placeholders})')
        params.extend(filter_vals)

    query = f'SELECT DISTINCT "{column}" FROM gold."{target_table}"'
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += f' ORDER BY "{column}"'

    cur.execute(query, params)
    raw_values = [row[0] for row in cur.fetchall() if row[0] is not None]
    conn.close()

    # Build value+label objects
    if column in LABEL_LOOKUPS:
        labels = _fetch_labels(column)
        return [
            {"value": str(v), "label": f"{v} - {labels.get(v, str(v))}"}
            for v in raw_values
        ]
    else:
        return [{"value": str(v), "label": str(v)} for v in raw_values]


# ---------------------------------------------------------------------------
# App schema: SQLite for users & selections
# ---------------------------------------------------------------------------

def get_app_connection():
    """SQLite connection for app-internal tables (users, selections)."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'app.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_app_schema():
    """Create the app tables in SQLite if they don't exist. Idempotent."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            table_name TEXT NOT NULL,
            columns TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, name)
        )
    """)
    conn.commit()
    conn.close()


# -- User queries -----------------------------------------------------------

def get_user_by_username(username):
    """Returns {"id", "username", "password_hash"} or None."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "password_hash": row[2]}


def get_user_by_id(user_id):
    """Returns {"id", "username", "created_at"} or None."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "created_at": row[2]}


def create_user(username, password_hash):
    """Insert a new user. Returns {"id", "username"}. Raises on duplicate."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": user_id, "username": username}


def delete_user(user_id):
    """Delete a user by id. Returns True if deleted, False if not found."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def list_users():
    """Return all users as list of {"id", "username", "created_at"}."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, created_at FROM users ORDER BY id")
    users = [
        {"id": row[0], "username": row[1], "created_at": row[2]}
        for row in cur.fetchall()
    ]
    conn.close()
    return users


# -- Selection queries ------------------------------------------------------

def get_user_selections(user_id):
    """Returns {name: {"table": ..., "columns": [...], "created_at": ...}}."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, table_name, columns, created_at FROM user_selections WHERE user_id = ? ORDER BY name",
        (user_id,),
    )
    selections = {}
    for row in cur.fetchall():
        selections[row[0]] = {
            "table": row[1],
            "columns": json.loads(row[2]),
            "created_at": row[3],
        }
    conn.close()
    return selections


def save_user_selection(user_id, name, table, columns):
    """Upsert a selection for a user. columns is a list of strings."""
    conn = get_app_connection()
    cur = conn.cursor()
    columns_json = json.dumps(columns)
    cur.execute("""
        INSERT INTO user_selections (user_id, name, table_name, columns)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (user_id, name)
        DO UPDATE SET table_name = EXCLUDED.table_name,
                      columns = EXCLUDED.columns,
                      created_at = datetime('now')
    """, (user_id, name, table, columns_json))
    conn.commit()
    conn.close()


def delete_user_selection(user_id, name):
    """Delete a selection by user_id and name. Returns True if deleted."""
    conn = get_app_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM user_selections WHERE user_id = ? AND name = ?",
        (user_id, name),
    )
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
