# run_select flow

One `run_select` call through the three read-only layers: the text guard, the read-only connection and the authorizer. Drawn from [server.py](../../server.py), [db.py](../../db.py) and [sql_guard.py](../../sql_guard.py).

```mermaid
sequenceDiagram
    participant C as MCP client
    participant S as server.run_select
    participant F as server._safe
    participant D as db.run_select
    participant G as sql_guard.check_select
    participant Q as SQLite (mode=ro + authorizer)

    C->>S: run_select(sql, limit)
    S->>F: _safe(db.run_select, sql, limit)
    F->>D: run_select(sql, limit=limit)
    D->>G: check_select(sql)
    alt empty, two statements, or first word not SELECT/WITH
        G-->>D: raise RejectedQuery
        D-->>F: RejectedQuery
        F-->>C: ValueError with the message
    else passes the text check
        G-->>D: cleaned sql
        D->>D: limit = max(1, min(limit, 500))
        D->>Q: connect() and set_progress_handler (5 s deadline)
        D->>Q: execute(sql, params)
        alt authorizer denies an action, or bad SQL
            Q-->>D: sqlite3.Error
            D-->>F: sqlite3.Error
            F-->>C: ValueError "SQL error: ..."
        else deadline passed
            Q-->>D: OperationalError "interrupted"
            D-->>F: TimeoutError
            F-->>C: ValueError with the message
        else query runs
            Q-->>D: fetchmany(limit + 1)
            D->>Q: close()
            D-->>F: columns, rows, row_count, truncated
            F-->>C: result dict
        end
    end
```

A query like `WITH x AS (SELECT 1) DELETE ...` passes `check_select` because it starts with `WITH`. The authorizer then denies the delete, which is the second `alt` branch.
