"""MCP server exposing a read-only view of the bookstore database (stdio)."""
from mcp.server.fastmcp import FastMCP

import db
from sql_guard import RejectedQuery

mcp = FastMCP("bookstore-sql")

# Revenue only counts completed orders, in cents, shown as dollars.
_REVENUE = "SUM(oi.quantity * oi.unit_price_cents) / 100.0"


def _safe(fn, *args, **kwargs):
    """Turn expected failures into a clean error message for the client."""
    try:
        return fn(*args, **kwargs)
    except (RejectedQuery, ValueError, TimeoutError) as e:
        raise ValueError(str(e)) from None


@mcp.tool()
def list_tables() -> list[str]:
    """List the tables in the bookstore database."""
    return db.list_tables()


@mcp.tool()
def describe_table(table: str) -> dict:
    """Show columns, foreign keys and row count for one table."""
    return _safe(db.describe_table, table)


@mcp.tool()
def run_select(sql: str, limit: int = db.DEFAULT_ROWS) -> dict:
    """Run one read-only SELECT (or WITH ... SELECT). Anything else is rejected.
    Returns at most `limit` rows (max 500). Stops after 5 seconds."""
    return _safe(db.run_select, sql, limit=limit)


@mcp.tool()
def monthly_sales(year: int | None = None) -> dict:
    """Revenue and order count per month for completed orders. Optional year filter."""
    sql = (
        "SELECT substr(o.ordered_on, 1, 7) AS month, COUNT(DISTINCT o.order_id) AS orders, "
        f"ROUND({_REVENUE}, 2) AS revenue FROM orders o JOIN order_items oi ON oi.order_id = o.order_id "
        "WHERE o.status = 'completed' AND (? IS NULL OR substr(o.ordered_on, 1, 4) = ?) "
        "GROUP BY month ORDER BY month"
    )
    y = None if year is None else str(year)
    return db.run_select(sql, (y, y), limit=db.MAX_ROWS)


@mcp.tool()
def top_books(limit: int = 10) -> dict:
    """Best-selling books by revenue (completed orders only)."""
    sql = (
        f"SELECT b.title, a.name AS author, SUM(oi.quantity) AS units, ROUND({_REVENUE}, 2) AS revenue "
        "FROM order_items oi JOIN orders o ON o.order_id = oi.order_id "
        "JOIN books b ON b.book_id = oi.book_id JOIN authors a ON a.author_id = b.author_id "
        "WHERE o.status = 'completed' GROUP BY b.book_id ORDER BY revenue DESC"
    )
    return db.run_select(sql, limit=limit)


@mcp.tool()
def low_stock(threshold: int = 5) -> dict:
    """Books whose stock on hand (sum of inventory movements) is at or below the threshold."""
    sql = (
        "SELECT b.title, SUM(m.quantity_change) AS stock FROM books b "
        "JOIN inventory_movements m ON m.book_id = b.book_id "
        "GROUP BY b.book_id HAVING stock <= ? ORDER BY stock, b.title"
    )
    return db.run_select(sql, (threshold,))


@mcp.tool()
def top_customers(limit: int = 10) -> dict:
    """Customers who spent the most on completed orders."""
    sql = (
        "SELECT c.first_name || ' ' || c.last_name AS customer, c.city, "
        f"COUNT(DISTINCT o.order_id) AS orders, ROUND({_REVENUE}, 2) AS spent "
        "FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
        "JOIN order_items oi ON oi.order_id = o.order_id "
        "WHERE o.status = 'completed' GROUP BY c.customer_id ORDER BY spent DESC"
    )
    return db.run_select(sql, limit=limit)


@mcp.resource("schema://bookstore")
def schema() -> str:
    """The CREATE statements of every table, as stored in the database."""
    r = db.run_select("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type DESC, name", limit=db.MAX_ROWS)
    return ";\n\n".join(row[0] for row in r["rows"]) + ";"


@mcp.prompt(title="Analyze sales by month")
def analyze_sales_by_month(year: str = "") -> str:
    """Ask the model to analyze monthly sales using this server's tools."""
    scope = f" for {year}" if year else ""
    return (
        f"Analyze sales by month{scope}. First call the monthly_sales tool"
        f"{' with year=' + year if year else ''}. Then report: the best and worst month, "
        "the month-to-month trend, and any month that looks unusual. "
        "If you need detail, use run_select. Say which numbers come from the tool "
        "and do not guess values you did not retrieve. Revenue counts completed orders only."
    )


if __name__ == "__main__":
    mcp.run()
