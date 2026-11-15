# Architecture

Components of the server and what each one does. Drawn from [server.py](../../server.py), [db.py](../../db.py) and [sql_guard.py](../../sql_guard.py).

```mermaid
flowchart LR
    client["MCP client<br/>(scripts/test_client.py or any MCP app)"]

    subgraph server["server.py (FastMCP app 'bookstore-sql')"]
        tools["Tools<br/>list_tables, describe_table, run_select,<br/>monthly_sales, top_books, low_stock, top_customers"]
        res["Resource<br/>schema://bookstore"]
        prompt["Prompt<br/>analyze_sales_by_month"]
        safe["_safe()<br/>turns errors into ValueError"]
    end

    subgraph guard["sql_guard.py"]
        check["check_select()"]
        strip["_strip()"]
        rej["RejectedQuery"]
    end

    subgraph dbmod["db.py"]
        runsel["run_select()<br/>row cap, 5 s timeout"]
        connect["connect()<br/>mode=ro + _authorizer"]
        helpers["list_tables(), describe_table()"]
    end

    sqlite[("data/bookstore.db<br/>or path in BOOKSTORE_DB")]

    client -- "stdio" --> server
    tools --> safe
    safe --> runsel
    safe --> helpers
    helpers --> runsel
    res --> runsel
    runsel --> check
    check --> strip
    check -. "raises" .-> rej
    runsel --> connect
    connect --> sqlite
```

The prompt only returns text. It does not touch the database.

Every query, including the fixed ones in `monthly_sales`, `top_books`, `low_stock`, `top_customers`, `describe_table` and the schema resource, goes through `db.run_select`. There is no other path to SQLite.
