import sqlite3
import os
from typing import List, Dict, Any, Optional

class SQLiteTool:
    def __init__(self, db_path: str = "data/northwind.sqlite"):
        self.db_path = db_path

    def get_schema(self) -> str:
        """Returns the schema of the database."""
        schema = ""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get list of tables and views
            cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'")
            items = cursor.fetchall()
            
            for name, type_ in items:
                schema += f"{type_.upper()}: {name}\n"
                cursor.execute(f"PRAGMA table_info('{name}')")
                columns = cursor.fetchall()
                for col in columns:
                    # cid, name, type, notnull, dflt_value, pk
                    schema += f"  - {col[1]} ({col[2]})\n"
                schema += "\n"
                
            conn.close()
        except Exception as e:
            return f"Error getting schema: {e}"
        return schema

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Executes a SQL query and returns the results."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Use a row factory to get dictionary-like results
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description] if cursor.description else []
            results = [dict(row) for row in rows]
            
            conn.close()
            return {
                "columns": columns,
                "rows": results,
                "error": None
            }
        except Exception as e:
            return {
                "columns": [],
                "rows": [],
                "error": str(e)
            }
