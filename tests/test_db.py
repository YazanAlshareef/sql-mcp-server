import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db  # noqa: E402


def test_blob_values_are_json_safe():
    r = db.run_select("SELECT x'0102' AS b")
    assert r["rows"] == [["<blob 2 bytes>"]]
    json.dumps(r)


def test_database_path_with_space_and_hash(tmp_path, monkeypatch):
    folder = tmp_path / "a b#c"
    folder.mkdir()
    copy = folder / "x.db"
    shutil.copy(db.DB_PATH, copy)
    monkeypatch.setattr(db, "DB_PATH", copy)
    assert "books" in db.list_tables()


def test_list_tables_returns_more_than_default_rows(tmp_path, monkeypatch):
    import sqlite3
    path = tmp_path / "many.db"
    con = sqlite3.connect(path)
    for i in range(120):
        con.execute(f"CREATE TABLE t{i:03d} (id INTEGER)")
    con.commit()
    con.close()
    monkeypatch.setattr(db, "DB_PATH", path)
    assert len(db.list_tables()) == 120
    assert db.describe_table("t119")["table"] == "t119"
