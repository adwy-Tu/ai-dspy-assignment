import sqlite3
import os

db_path = os.path.join("data", "northwind.sqlite")

sql_commands = """
CREATE VIEW IF NOT EXISTS orders AS SELECT * FROM Orders;
CREATE VIEW IF NOT EXISTS order_items AS SELECT * FROM "Order Details";
CREATE VIEW IF NOT EXISTS products AS SELECT * FROM Products;
CREATE VIEW IF NOT EXISTS customers AS SELECT * FROM Customers;
"""

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(sql_commands)
    conn.commit()
    conn.close()
    print("Database views created successfully.")
except Exception as e:
    print(f"Error creating database views: {e}")
