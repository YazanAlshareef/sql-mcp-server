"""Direct tests for sql_guard edge cases."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sql_guard import RejectedQuery, check_select  # noqa: E402


@pytest.mark.parametrize("sql", [
    "SELECT 'unterminated",
    'SELECT "unterminated',
    "SELECT `unterminated",
    "SELECT [unterminated",
    "SELECT 1 /* unterminated",
])
def test_unterminated_input_is_rejected(sql):
    with pytest.raises(RejectedQuery):
        check_select(sql)


@pytest.mark.parametrize("sql", [
    "SELECT 'a;b' AS x",
    "SELECT [a;b] FROM t",
    "SELECT 'it''s; ok'",
    "SELECT 1 -- ; DROP TABLE t",
    "SELECT 1 /* ; */",
])
def test_semicolon_inside_literal_or_comment_is_allowed(sql):
    assert check_select(sql).startswith("SELECT")


def test_trailing_semicolon_is_trimmed():
    assert check_select("SELECT 1;  ") == "SELECT 1"


@pytest.mark.parametrize("sql", ["", "   ", None, 5])
def test_empty_or_non_string_is_rejected(sql):
    with pytest.raises(RejectedQuery):
        check_select(sql)
