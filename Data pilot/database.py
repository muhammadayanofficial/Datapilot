import os
import sqlite3

from contextlib import contextmanager
from datetime import date, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE_PATH = os.path.join(INSTANCE_DIR, "datapilot.db")

os.makedirs(INSTANCE_DIR, exist_ok=True)


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price > 0),
                sale_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        count = connection.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

        if count == 0:
            today = date.today()

            demo_sales = [
                ("Classic T-Shirt", "Apparel", 12, 1500, 0),
                ("Hoodie", "Apparel", 8, 3500, 1),
                ("Tote Bag", "Accessories", 20, 800, 1),
                ("Sneakers", "Footwear", 5, 6500, 2),
                ("Classic T-Shirt", "Apparel", 15, 1500, 2),
                ("Denim Jacket", "Apparel", 6, 4500, 3),
                ("Tote Bag", "Accessories", 10, 800, 4),
                ("Hoodie", "Apparel", 9, 3500, 4),
                ("Sneakers", "Footwear", 4, 6500, 5),
                ("Denim Jacket", "Apparel", 7, 4500, 6),
            ]

            rows = [
                (
                    name,
                    category,
                    quantity,
                    price,
                    (today - timedelta(days=days_ago)).isoformat(),
                )
                for name, category, quantity, price, days_ago
                in demo_sales
            ]

            connection.executemany(
                """
                INSERT INTO sales
                    (product_name, category, quantity, unit_price, sale_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )


def add_sale(product_name, category, quantity, unit_price, sale_date):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sales
                (product_name, category, quantity, unit_price, sale_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                product_name,
                category,
                quantity,
                unit_price,
                sale_date,
            ),
        )

        return cursor.lastrowid


def delete_sale(sale_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM sales WHERE id = ?",
            (sale_id,),
        )

        return cursor.rowcount > 0


def get_dashboard_data():
    with get_connection() as connection:
        metric_row = connection.execute("""
            SELECT
                COUNT(*) AS sale_records,
                COALESCE(SUM(quantity), 0) AS total_units,
                COALESCE(SUM(quantity * unit_price), 0)
                    AS total_revenue,
                COALESCE(AVG(quantity * unit_price), 0)
                    AS average_sale,
                COUNT(DISTINCT product_name) AS product_count
            FROM sales
        """).fetchone()

        product_rows = connection.execute("""
            SELECT
                product_name,
                category,
                SUM(quantity) AS units_sold,
                SUM(quantity * unit_price) AS revenue
            FROM sales
            GROUP BY product_name, category
            ORDER BY revenue DESC
        """).fetchall()

        category_rows = connection.execute("""
            SELECT
                category,
                SUM(quantity) AS units_sold,
                SUM(quantity * unit_price) AS revenue
            FROM sales
            GROUP BY category
            ORDER BY revenue DESC
        """).fetchall()

        sales_rows = connection.execute("""
            SELECT
                id,
                product_name,
                category,
                quantity,
                unit_price,
                quantity * unit_price AS revenue,
                sale_date
            FROM sales
            ORDER BY sale_date DESC, id DESC
            LIMIT 10
        """).fetchall()

        insight_rows = connection.execute("""
            SELECT id, question, answer, created_at
            FROM insights
            ORDER BY id DESC
            LIMIT 8
        """).fetchall()

    stats = dict(metric_row)

    return {
        "stats": stats,
        "products": [dict(row) for row in product_rows],
        "categories": [dict(row) for row in category_rows],
        "sales": [dict(row) for row in sales_rows],
        "insights": [dict(row) for row in insight_rows],
    }


def get_analytics_context():
    data = get_dashboard_data()

    return {
        "metrics": data["stats"],
        "product_performance": data["products"][:25],
        "category_performance": data["categories"],
        "recent_sales": data["sales"][:10],
    }


def save_insight(question, answer):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO insights (question, answer)
            VALUES (?, ?)
            """,
            (question, answer),
        )

        row = connection.execute(
            """
            SELECT id, question, answer, created_at
            FROM insights
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        return dict(row)