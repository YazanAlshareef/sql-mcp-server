"""Security tests: every write, schema change, ATTACH, PRAGMA write and
multi-statement trick must fail, and the database file must stay identical."""
import hashlib
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db  # noqa: E402
from sql_guard import RejectedQuery  # noqa: E402

BAD_QUERIES = {
    "insert": "INSERT INTO authors(name) VALUES ('x')",
    "update": "UPDATE books SET list_price_cents = 1",
    "delete": "DELETE FROM books",
    "drop table": "DROP TABLE books",
    "create table": "CREATE TABLE t(a)",
    "alter": "ALTER TABLE books ADD COLUMN x TEXT",
    "attach": "ATTACH DATABASE 'evil.db' AS evil",
    "pragma write": "PRAGMA user_version = 5",
    "pragma writable_schema": "PRAGMA writable_schema = 1",
    "pragma query_only off": "PRAGMA query_only = 0",
    "multi: select then drop": "SELECT 1; DROP TABLE books",
    "multi: select then insert": "SELECT 1; INSERT INTO authors(name) VALUES ('x')",
    "multi: semicolon after comment": "SELECT 1; -- harmless\nDELETE FROM books",
    "multi: semicolon hidden by comment trick": "SELECT 1 /* x */ ; /* y */ DROP TABLE books",
    "begin transaction": "BEGIN; SELECT 1",
    "vacuum": "VACUUM",
    "lowercase insert": "insert into authors(name) values ('x')",
    "leading comment then insert": "/* hi */ INSERT INTO authors(name) VALUES ('x')",
    "empty": "   ",
}


@pytest.fixture(scope="module", autouse=True)
def db_unchanged():
    before = hashlib.sha256(db.DB_PATH.read_bytes()).hexdigest()
    yield
    assert hashlib.sha256(db.DB_PATH.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("sql", BAD_QUERIES.values(), ids=BAD_QUERIES.keys())
def test_guard_rejects(sql):
    with pytest.raises(RejectedQuery):
        db.run_select(sql)


# Queries that look like SELECTs but write. The guard lets them through;
# the authorizer / read-only connection must stop them.
@pytest.mark.parametrize("sql", [
    "WITH x AS (SELECT 1) INSERT INTO authors(name) VALUES ('x')",
    "WITH x AS (SELECT 1) DELETE FROM books",
    "WITH x AS (SELECT 1) UPDATE books SET list_price_cents = 1",
])
def test_with_prefixed_writes_denied_by_sqlite(sql):
    with pytest.raises(sqlite3.DatabaseError):
        db.run_select(sql)


def test_connection_itself_is_read_only():
    conn = sqlite3.connect(f"file:{db.DB_PATH.as_posix()}?mode=ro", uri=True)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM books")


def test_authorizer_denies_writes_even_if_guard_skipped():
    conn = db.connect()
    for sql in ["DELETE FROM books", "ATTACH 'x.db' AS x", "PRAGMA query_only = 0", "DROP TABLE books"]:
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute(sql)


def test_semicolon_inside_string_is_fine():
    r = db.run_select("SELECT 'a;b' AS v")
    assert r["rows"] == [["a;b"]]


def test_trailing_semicolon_is_fine():
    assert db.run_select("SELECT 1;")["rows"] == [[1]]


def test_row_limit():
    r = db.run_select("SELECT * FROM order_items", limit=7)
    assert r["row_count"] == 7 and r["truncated"] is True


def test_row_limit_is_capped():
    r = db.run_select("SELECT * FROM order_items", limit=10**9)
    assert r["row_count"] == db.MAX_ROWS


def test_timeout():
    slow = "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) SELECT count(*) FROM c"
    with pytest.raises(TimeoutError):
        db.run_select(slow, timeout=0.3)


def test_describe_table_rejects_injection():
    with pytest.raises(ValueError):
        db.describe_table('books"; DROP TABLE books; --')
