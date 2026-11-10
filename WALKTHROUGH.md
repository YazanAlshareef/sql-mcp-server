# Walkthrough: every file in plain English

**The big picture:** an MCP client (an app with a model in it) starts `server.py` as a child process and talks to it over stdin/stdout. It asks "what tools do you have?" and then calls them. Each tool reads the bookstore SQLite file and sends back rows. Nothing can write.

## `server.py`
The MCP side. Uses `FastMCP`; each `@mcp.tool()` function becomes a tool, with its docstring as the description and its type hints as the input schema.
- `list_tables`, `describe_table`, `run_select`: thin wrappers around `db.py`.
- `monthly_sales`, `top_books`, `low_stock`, `top_customers`: fixed SQL for common questions. Values from the client (year, threshold) are passed as bound parameters (`?`), never pasted into the SQL string.
- `schema()` is a *resource*: read-only data the client can load (`schema://bookstore`).
- `analyze_sales_by_month` is a *prompt*: a ready-made instruction telling the model to use `monthly_sales` first.
- `_safe` converts my own errors into a clean message for the client.

## `db.py`
All database access.
- `connect()` opens SQLite with `mode=ro` and installs the authorizer (an allow-list of action types).
- `run_select()` checks the SQL with the guard, caps rows with `fetchmany(limit + 1)` (the extra row tells me if the result was truncated), and sets a progress handler that aborts after 5 seconds.
- `describe_table()` only accepts names that exist in `sqlite_master`, so the table name in the `COUNT(*)` statement cannot be an injection.

## `sql_guard.py`
Text check before SQLite sees the query. `_strip` walks the string and removes comments and the insides of quoted strings, so `SELECT 'a;b'` is fine but `SELECT 1; DROP TABLE x` is not. `check_select` then requires one statement starting with `SELECT` or `WITH`. This is the *first* layer; the read-only connection and the authorizer are the real safety net.

## `tests/test_security.py`
Proves the rules. Parametrized bad queries (INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, ATTACH, PRAGMA writes, multi-statement tricks, comment tricks) must all raise. `WITH ... DELETE` passes the text guard on purpose and must be stopped by SQLite. Also tests the row cap, the timeout (an endless recursive query), injection through `describe_table`, and that the database file hash is identical after all tests.

## `scripts/test_client.py`
A tiny MCP client. Launches `server.py`, lists tools/resources/prompts, calls every tool, tries four attacks, reads the resource, fetches the prompt. Output is saved in `docs/sample_client_output.txt`.

## `data/bookstore.db`
Copy of the synthetic database from `sql-bookstore-analytics` (8 tables: authors, categories, suppliers, books, customers, orders, order_items, inventory_movements). Money is integer cents.

## Other files
- `requirements.txt`: the `mcp` SDK and `pytest`.
- `.gitignore`, `LICENSE` (MIT).
- `README.md`: what / how / limits.

## Questions I should be able to answer
- *Why three layers?* Text parsing is easy to get wrong; SQLite's own enforcement is not.
- *Why is `WITH` risky?* In SQLite a CTE can prefix an INSERT/UPDATE/DELETE, so "starts with WITH" alone is not enough. The authorizer blocks it.
- *Why allow two pragmas?* `pragma_table_info` is how `describe_table` reads columns, and it counts as a PRAGMA action.
- *What would I add for real use?* Table and column allow-lists, auth for a remote transport, query logging.
