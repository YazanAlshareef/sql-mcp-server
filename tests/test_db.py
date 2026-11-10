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
