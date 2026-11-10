"""Starts server.py over stdio and calls every tool, the resource and the prompt.
Run from the repo root:  python scripts/test_client.py"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")], cwd=str(ROOT))


def show(title, result):
    print(f"\n=== {title}")
    if result.isError:
        print("ERROR:", result.content[0].text)
        return
    text = " | ".join(b.text for b in result.content)  # a list result comes back as one block per item
    text = " ".join(text.split())
    print(text if len(text) < 500 else text[:500] + " ...")


async def main():
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            print("tools:", [t.name for t in (await s.list_tools()).tools])
            print("resources:", [str(r.uri) for r in (await s.list_resources()).resources])
            print("prompts:", [p.name for p in (await s.list_prompts()).prompts])

            show("list_tables", await s.call_tool("list_tables", {}))
            show("describe_table(books)", await s.call_tool("describe_table", {"table": "books"}))
            show("run_select", await s.call_tool("run_select", {"sql": "SELECT title, list_price_cents FROM books ORDER BY list_price_cents DESC", "limit": 3}))
            show("monthly_sales(2025)", await s.call_tool("monthly_sales", {"year": 2025}))
            show("top_books(3)", await s.call_tool("top_books", {"limit": 3}))
            show("low_stock(3)", await s.call_tool("low_stock", {"threshold": 3}))
            show("top_customers(3)", await s.call_tool("top_customers", {"limit": 3}))
            print("\n--- attacks (each must be an error) ---")
            for sql in ["DROP TABLE books", "SELECT 1; DELETE FROM books", "ATTACH 'x.db' AS x", "PRAGMA user_version = 9"]:
                show(f"run_select({sql!r})", await s.call_tool("run_select", {"sql": sql}))

            res = await s.read_resource("schema://bookstore")
            print("\n=== resource schema://bookstore (first 200 chars)\n" + res.contents[0].text[:200])
            p = await s.get_prompt("analyze_sales_by_month", {"year": "2025"})
            print("\n=== prompt analyze_sales_by_month\n" + p.messages[0].content.text)


asyncio.run(main())
