"""Compare the business tools with the sample output in the bookstore repo
(queries 02_top_books_by_revenue.sql and 06_top_customers.sql, seed 42 data)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server  # noqa: E402

Q02 = [
    ("The Last River", "Ava Patel", 320, 7578.4),
    ("The Lost River", "Amir Garcia", 146, 5168.14),
    ("The Hidden Orchard", "Liam Cohen", 196, 4634.84),
    ("The Salt River", "Mia Fox", 111, 3499.69),
    ("The Red Garden", "Ava Cohen", 85, 3107.15),
    ("The Silver Archive", "Oscar Patel", 104, 2971.46),
    ("The Paper Engine", "Ethan Singh", 88, 2779.92),
    ("The Broken Orchard", "Noah Novak", 79, 2426.51),
    ("The Lost Letter", "Chloe Khan", 42, 1390.18),
    ("The Silver Kitchen", "Ava Hughes", 43, 1265.57),
]
Q06 = [
    ("Omar Kim", "Geelong", 43, 2249.9), ("Yuki Park", "Melbourne", 42, 1955.49),
    ("Isla Fox", "Melbourne", 42, 1919.2), ("Amir Chen", "Melbourne", 44, 1670.7),
    ("Ruby Cohen", "Hobart", 37, 1665.41), ("Noah Clarke", "Brisbane", 35, 1520.23),
    ("Ava Wilson", "Adelaide", 26, 1334.86), ("Mateo Khan", "Melbourne", 25, 1208.02),
    ("Sam Haddad", "Brisbane", 21, 1051.8), ("Liam Novak", "Canberra", 19, 939.21),
]


def test_top_books_matches_q02():
    assert [tuple(r) for r in server.top_books(10)["rows"]] == Q02


def test_top_customers_matches_q06():
    assert [tuple(r) for r in server.top_customers(10)["rows"]] == Q06
