# Data model

Tables of the bookstore SQLite database and their foreign keys. Taken from the `CREATE TABLE` statements stored in [data/bookstore.db](../../data/bookstore.db) (also served by the `schema://bookstore` resource in [server.py](../../server.py)). The queries that use these tables are in [server.py](../../server.py).

```mermaid
erDiagram
    authors ||--o{ books : "author_id"
    categories ||--o{ books : "category_id"
    customers ||--o{ orders : "customer_id"
    orders ||--|{ order_items : "order_id"
    books ||--o{ order_items : "book_id"
    books ||--o{ inventory_movements : "book_id"
    suppliers |o--o{ inventory_movements : "supplier_id"
    orders |o--o{ inventory_movements : "order_id"

    authors {
        INTEGER author_id PK
        TEXT name
    }
    categories {
        INTEGER category_id PK
        TEXT name
    }
    suppliers {
        INTEGER supplier_id PK
        TEXT name
        TEXT email
        TEXT country
    }
    books {
        INTEGER book_id PK
        TEXT isbn
        TEXT title
        INTEGER author_id FK
        INTEGER category_id FK
        INTEGER list_price_cents
        INTEGER published_year
    }
    customers {
        INTEGER customer_id PK
        TEXT first_name
        TEXT last_name
        TEXT email
        TEXT city
        TEXT joined_on
    }
    orders {
        INTEGER order_id PK
        INTEGER customer_id FK
        TEXT ordered_on
        TEXT channel
        TEXT status
    }
    order_items {
        INTEGER order_id PK
        INTEGER book_id PK
        INTEGER quantity
        INTEGER unit_price_cents
    }
    inventory_movements {
        INTEGER movement_id PK
        INTEGER book_id FK
        TEXT moved_on
        TEXT movement_type
        INTEGER quantity_change
        INTEGER supplier_id FK
        INTEGER unit_cost_cents
        INTEGER order_id FK
    }
```

`inventory_movements` also has a composite foreign key `(order_id, book_id)` to `order_items`. The diagram shows the two single-column links.
