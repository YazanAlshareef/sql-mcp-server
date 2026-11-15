# Walkthrough: every file

An MCP client (an app with a model in it) starts `server.py` as a child process and talks to it over stdin and stdout. It asks what tools exist, then calls them. Each tool reads the bookstore SQLite file and sends back rows. Nothing can write.

## `server.py`
The MCP side, built on `FastMCP`. Each `@mcp.tool()` function becomes a tool: the docstring is its description and the type hints are its input schema.
- `list_tables`, `describe_table`, `run_select` are thin wrappers around `db.py`.
- `monthly_sales`, `top_books`, `low_stock`, `top_customers` hold fixed SQL for common questions. Values from the client (year, threshold) go in as bound parameters (`?`), never pasted into the SQL string. Revenue and customer rankings break ties by name so the order is stable.
- Every tool goes through `_safe`. It turns my own errors and SQLite errors into one clean `ValueError`, so the client sees "SQL error: no such table" and not a stack trace.
- `schema()` is a resource: read-only data the client can load (`schema://bookstore`).
- `analyze_sales_by_month` is a prompt, a ready-made instruction that tells the model to call `monthly_sales` first.

## `db.py`
All database access.
- `connect()` opens SQLite with `mode=ro` and installs the authorizer, an allow-list of action types.
- `run_select()` checks the SQL with the guard, caps rows with `fetchmany(limit + 1)` (the extra row tells me whether the result was cut off), and sets a progress handler that aborts after 5 seconds.
- `describe_table()` only accepts names found in `sqlite_master`, so the table name in the `COUNT(*)` statement cannot carry an injection.

## `sql_guard.py`
A text check that runs before SQLite sees the query. `_strip` walks the string and removes comments and the insides of quoted strings, so `SELECT 'a;b'` passes and `SELECT 1; DROP TABLE x` does not. `check_select` then wants one statement that starts with `SELECT` or `WITH`. This is the first layer. The read-only connection and the authorizer are the real safety net.

## `tests/test_security.py`
The security proof. Bad queries (INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, ATTACH, PRAGMA writes, multi-statement tricks, comment tricks) must all raise. `WITH ... DELETE` passes the text guard on purpose and SQLite has to stop it. It also covers `randomblob` and `zeroblob`, the row cap, the timeout (an endless recursive query), injection through `describe_table`, and a check that the database file hash is the same after the tests.

## `tests/test_db.py` and `tests/test_business.py`
`test_db.py`: BLOBs become `<blob N bytes>`, and the database still opens from a folder named `a b#c`.
`test_business.py`: `top_books` and `top_customers` must equal the sample output of queries Q02 and Q06 in the bookstore repo. It also checks that SQLite errors reach the client as `ValueError` and that ties are ordered by name.

## `scripts/test_client.py`
A small MCP client. It launches `server.py`, lists tools, resources and prompts, calls every tool, tries four attacks, reads the resource and fetches the prompt.

## `docs/sample_client_output.txt`
Saved output of `scripts/test_client.py`. I re-ran the script after the last code change and the output was identical. It is evidence for the README, not code.

## `.github/workflows/ci.yml`
Runs `pip install -r requirements.txt`, `python -m pytest -q` and `python scripts/test_client.py` on every push to main and on pull requests. No secrets. I ran the same three commands locally first.

## `data/bookstore.db`
Copy of the synthetic database from `sql-bookstore-analytics`: 8 tables (authors, categories, suppliers, books, customers, orders, order_items, inventory_movements). Money is stored as integer cents.

## Other files
`requirements.txt` (the `mcp` SDK and `pytest`), `.gitignore`, `LICENSE` (MIT), `README.md`.

## Questions I should be able to answer
- *Why three layers?* Text parsing is easy to get wrong. SQLite's own enforcement is not.
- *Why is `WITH` risky?* In SQLite a CTE can prefix an INSERT, UPDATE or DELETE, so "starts with WITH" is not enough. The authorizer blocks it.
- *Why allow two pragmas?* `pragma_table_info` is how `describe_table` reads columns, and SQLite counts it as a PRAGMA action.
- *Why break ties by name?* Several books earn the same revenue. Without a tie-breaker the order is up to SQLite and can change.
- *What would I add for real use?* Table and column allow-lists, authentication for a remote transport, and query logging.
