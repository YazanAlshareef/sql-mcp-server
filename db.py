"""Read-only access to the bookstore SQLite file."""
import os
import sqlite3
import time
from pathlib import Path

from sql_guard import check_select

DB_PATH = Path(os.environ.get("BOOKSTORE_DB", Path(__file__).parent / "data" / "bookstore.db"))
MAX_ROWS = 500
DEFAULT_ROWS = 100
TIMEOUT_SECONDS = 5.0

# Only these SQLite action codes may run. Anything else (INSERT, UPDATE,
# DELETE, CREATE, DROP, ALTER, ATTACH, PRAGMA, TRANSACTION...) is denied.
_ALLOWED = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}


# Table-valued pragma functions count as PRAGMA actions. These two only read
# schema info and are needed by describe_table; every other pragma is denied.
_SAFE_PRAGMAS = {"table_info", "foreign_key_list"}


def _authorizer(action, arg1, *_):
    if action in _ALLOWED:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_PRAGMA and arg1 in _SAFE_PRAGMAS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def connect() -> sqlite3.Connection:
    # mode=ro: SQLite itself refuses writes, even if the guard had a bug.
    conn = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.set_authorizer(_authorizer)
    return conn


def run_select(sql: str, params=(), limit: int = DEFAULT_ROWS, timeout: float = TIMEOUT_SECONDS) -> dict:
    """Run one guarded SELECT. Returns columns, rows, truncated flag."""
    sql = check_select(sql)
    limit = max(1, min(int(limit), MAX_ROWS))
    conn = connect()
    try:
        deadline = time.monotonic() + timeout
        # Returning non-zero from the handler aborts the running query.
        conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10000)
        cur = conn.execute(sql, params)
        rows = cur.fetchmany(limit + 1)
        columns = [d[0] for d in cur.description or []]
        truncated = len(rows) > limit
        return {
            "columns": columns,
            "rows": [list(r) for r in rows[:limit]],
            "row_count": min(len(rows), limit),
            "truncated": truncated,
        }
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e):
            raise TimeoutError(f"query stopped after {timeout} seconds") from e
        raise
    finally:
        conn.close()


def list_tables() -> list[str]:
    r = run_select("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    return [row[0] for row in r["rows"]]


def describe_table(name: str) -> dict:
    # Table name is checked against the real list, then passed as a bound parameter.
    if name not in list_tables():
        raise ValueError(f"unknown table: {name}")
    cols = run_select(
        "SELECT name, type, \"notnull\" AS not_null, pk FROM pragma_table_info(?)", (name,), limit=MAX_ROWS
    )
    fks = run_select(
        "SELECT \"from\" AS column_name, \"table\" AS ref_table, \"to\" AS ref_column FROM pragma_foreign_key_list(?)",
        (name,), limit=MAX_ROWS,
    )
    count = run_select(f'SELECT COUNT(*) FROM "{name}"')["rows"][0][0]
    return {
        "table": name,
        "row_count": count,
        "columns": [dict(zip(cols["columns"], r)) for r in cols["rows"]],
        "foreign_keys": [dict(zip(fks["columns"], r)) for r in fks["rows"]],
    }
