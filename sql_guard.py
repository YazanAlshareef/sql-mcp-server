"""Checks a SQL string before it reaches SQLite. First line of defence.

The second line is db.py: read-only connection plus an authorizer.
Neither one alone is trusted.
"""


class RejectedQuery(ValueError):
    pass


def _strip(sql: str) -> str:
    """Remove comments and string/identifier contents so keyword checks
    cannot be fooled by text inside a literal. Returns the skeleton."""
    out = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c == "-" and sql[i:i + 2] == "--":
            j = sql.find("\n", i)
            i = n if j == -1 else j
            out.append(" ")
        elif c == "/" and sql[i:i + 2] == "/*":
            j = sql.find("*/", i + 2)
            if j == -1:
                raise RejectedQuery("unterminated comment")
            i = j + 2
            out.append(" ")
        elif c in "'\"`":
            j = i + 1
            while True:
                j = sql.find(c, j)
                if j == -1:
                    raise RejectedQuery("unterminated quote")
                if sql[j:j + 2] == c * 2:  # doubled quote = escaped quote
                    j += 2
                    continue
                break
            out.append(c + c)
            i = j + 1
        elif c == "[":
            j = sql.find("]", i)
            if j == -1:
                raise RejectedQuery("unterminated bracket")
            out.append("[]")
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def check_select(sql: str) -> str:
    """Return the cleaned query if it is a single SELECT, else raise."""
    if not isinstance(sql, str) or not sql.strip():
        raise RejectedQuery("empty query")
    skeleton = _strip(sql).strip()
    body = skeleton.rstrip("; \t\r\n")
    if ";" in body:
        raise RejectedQuery("only one statement is allowed")
    first = body.split(None, 1)[0].upper() if body else ""
    if first not in ("SELECT", "WITH"):
        raise RejectedQuery("only SELECT queries are allowed")
    return sql.strip().rstrip(";").strip()
