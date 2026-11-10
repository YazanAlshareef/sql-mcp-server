# sql-mcp-server

A small [Model Context Protocol](https://modelcontextprotocol.io) server that lets an MCP client ask questions about a SQLite bookstore database, **read-only**. The client can list tables, describe them, run `SELECT` queries, and call a few ready-made business-question tools.

The data is a copy of the synthetic database from my `sql-bookstore-analytics` project (made-up names, `@example.com` emails, fake ISBNs). Nothing here is real customer data.

## What it exposes

| Kind | Name | What it does |
|---|---|---|
| tool | `list_tables` | table names |
| tool | `describe_table` | columns, foreign keys, row count |
| tool | `run_select` | one `SELECT` / `WITH ... SELECT`, max 500 rows, 5 second timeout |
| tool | `monthly_sales` | revenue and orders per month (optional year) |
| tool | `top_books` | best sellers by revenue |
| tool | `low_stock` | books at or below a stock threshold |
| tool | `top_customers` | biggest spenders |
| resource | `schema://bookstore` | the `CREATE TABLE` statements |
| prompt | `analyze_sales_by_month` | asks the model to analyze monthly sales using the tools |

Revenue counts `completed` orders only: `quantity * unit_price_cents`, shown in dollars. Stock is the sum of `inventory_movements.quantity_change` (the source database never stores stock directly).

## Why Python

I used the official Python SDK (`mcp`, its `FastMCP` helper). SQLite support is in the standard library (`sqlite3`), so the only dependency is the SDK, and my other portfolio projects are Python too. It is built against `mcp` 1.30 (`requirements.txt` allows 1.30 up to, but not including, 2).

## How it stays read-only

Three independent layers, so one bug is not enough:

1. `sql_guard.py` strips comments and string contents, rejects a `;` in the middle, and requires the first word to be `SELECT` or `WITH`.
2. The database is opened with SQLite `mode=ro`. SQLite itself refuses writes.
3. A SQLite authorizer allows only select/read/function actions. `INSERT`, `DELETE`, `ATTACH`, `PRAGMA`, etc. are denied even if they get past layer 1 (for example `WITH x AS (...) DELETE ...`).

`randomblob` and `zeroblob` are also denied (they can allocate huge values in one call). BLOB values in results are shown as `<blob N bytes>` so they can be sent as JSON.

Plus a row cap (500 max, 100 default) and a 5 second timeout via a progress handler.

## How to run

```bash
pip install -r requirements.txt
python -m pytest -q            # 37 security and behaviour tests
python scripts/test_client.py  # starts the server over stdio and calls everything
```

Real output of the test client is in [docs/sample_client_output.txt](docs/sample_client_output.txt).

### Connect an MCP client

Most MCP-compatible desktop apps take a JSON entry like this (use your own absolute path):

```json
{
  "mcpServers": {
    "bookstore-sql": {
      "command": "python",
      "args": ["C:/path/to/sql-mcp-server/server.py"]
    }
  }
}
```

Set the `BOOKSTORE_DB` environment variable to use a different SQLite file.

## How an AI coding assistant helped

An AI coding assistant wrote the first draft of the code and tests from my brief. I chose the scope (read-only, SELECT-only, which tools) and I review and run everything. [WALKTHROUGH.md](WALKTHROUGH.md) explains each file so I can defend it.

## What broke and how it got fixed

- **`describe_table` was denied by the authorizer.** `pragma_table_info(...)` counts as a `PRAGMA` action, and I had denied all pragmas. Fix: allow only `table_info` and `foreign_key_list`; every other pragma stays denied.
- **Tool results showed up empty in my first client script.** FastMCP only fills `structuredContent` for typed returns, and several tools return plain dicts. Fix: the client reads the text content instead.
- **Database path in the SQLite URI.** An f-string path would break with `?` or `#` in the folder name. Fix: build the URI with `Path.as_uri()` (covered by `tests/test_db.py`, which copies the database into a folder named `a b#c`).

## Limits

- SQLite only; the dialect is SQLite's.
- The 5 second timeout stops CPU-heavy queries, but a query can still use memory until then.
- `run_select` can read every column in the database, including the synthetic customer emails. Fine for fake data, but do not point this at a real database without adding table and column allow-lists.
- stdio transport only. No authentication, because it runs as a local process for one user.
- Tested with my own Python client script. I have not tested it inside a desktop MCP app yet.
- `top_books` and `top_customers` are tested against the sample output of queries Q02 and Q06 in the bookstore repo (`tests/test_business.py`). `monthly_sales` and `low_stock` are not cross-checked.

## License

MIT
