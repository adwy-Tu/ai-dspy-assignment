import json
import requests
from agent.tools.sqlite_tool import SQLiteTool
from agent.rag.retrieval import Retrieval

class SimpleAgent:
    def __init__(self):
        self.sqlite_tool = SQLiteTool()
        self.retrieval = Retrieval()
        self.schema = self.sqlite_tool.get_schema()
        self.api_url = "http://localhost:11434/api/generate"
        self.model = "llama3.2:3b"  # Recommended: 2x better than phi3.5

    def _call_llm(self, prompt, format="json"):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": format,
            "options": {
                "temperature": 0.1, # Low temperature for deterministic output
                "num_ctx": 4096
            }
        }
        try:
            response = requests.post(self.api_url, json=payload)
            return response.json()['response']
        except Exception as e:
            print(f"LLM Call Error: {e}")
            return "{}"

    def _clean_sql(self, sql):
        # Remove markdown code blocks
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Fix common dialect issues
        if "YEAR(" in sql:
            sql = sql.replace("YEAR(", "strftime('%Y', ")
        if "MONTH(" in sql:
            sql = sql.replace("MONTH(", "strftime('%m', ")
        if "NOW()" in sql:
            sql = sql.replace("NOW()", "date('now')")
            
        # Remove invalid characters (like the $$$ seen in logs)
        sql = sql.replace("$$$", "_")
        
        return sql

    def _validate_sql(self, sql):
        """Check if SQL query is valid and complete."""
        if not sql or len(sql.strip()) < 10:
            return False
        
        sql_upper = sql.upper()
        
        # Must have SELECT and FROM
        if "SELECT" not in sql_upper or "FROM" not in sql_upper:
            return False
        
        # Check for incomplete queries (common signs)
        if sql.endswith("...") or sql.endswith("--"):
            return False
        
        # Check for unfinished WHERE/JOIN clauses
        if sql.rstrip().endswith(("WHERE", "AND", "OR", "JOIN", "ON")):
            return False
            
        return True

    def _parse_json(self, text):
        import re
        try:
            # Try direct parse
            return json.loads(text)
        except:
            # Try to find JSON object in text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            return {}

    def generate_sql(self, question):
        prompt = f"""You are a SQLite expert. Generate a query based on examples.
        
        Schema:
        {self.schema}
        
        Examples:
        Q: "What is the total revenue in 1997?"
        A: {{"sql": "SELECT SUM(UnitPrice * Quantity) FROM OrderDetails od JOIN Orders o ON od.OrderID = o.OrderID WHERE strftime('%Y', o.OrderDate) = '1997'"}}
        
        Q: "Which category sold the most in June 1997?"
        A: {{"sql": "SELECT c.CategoryName, SUM(od.Quantity) as Total FROM Categories c JOIN Products p ON c.CategoryID = p.CategoryID JOIN OrderDetails od ON p.ProductID = od.ProductID JOIN Orders o ON od.OrderID = o.OrderID WHERE strftime('%Y-%m', o.OrderDate) = '1997-06' GROUP BY c.CategoryName ORDER BY Total DESC LIMIT 1"}}
        
        Q: "Top 3 products by revenue?"
        A: {{"sql": "SELECT p.ProductName, SUM(od.UnitPrice * od.Quantity * (1 - COALESCE(od.Discount, 0))) as Revenue FROM Products p JOIN OrderDetails od ON p.ProductID = od.ProductID GROUP BY p.ProductID, p.ProductName ORDER BY Revenue DESC LIMIT 3"}}
        
        Now generate for: "{question}"
        Return JSON: {{"sql": "..."}}
        """
        
        response = self._call_llm(prompt)
        data = self._parse_json(response)
        sql = data.get("sql", "")
        sql = self._clean_sql(sql)
        
        # Validate before returning
        if not self._validate_sql(sql):
            print(f"Invalid SQL generated, skipping: {sql[:100]}")
            return ""
            
        return sql

    def synthesize(self, question, sql_result, docs, format_hint):
        # Determine if we have SQL results
        has_sql_data = sql_result.get("rows") and len(sql_result["rows"]) > 0
        
        if has_sql_data:
            prompt = f"""Extract the answer from SQL results.
            
            Question: {question}
            Format: {format_hint}
            SQL Results: {json.dumps(sql_result["rows"])}
            
            Return JSON: {{"final_answer": <value>, "citations": ["table_name"]}}
            """
        else:
            prompt = f"""Answer from documents.
            
            Question: {question}
            Format: {format_hint}
            Documents: {json.dumps(docs)}
            
            Extract the answer from document content. Return JSON: {{"final_answer": <value>, "citations": [<doc_ids>]}}
            """
        
        response = self._call_llm(prompt)
        return self._parse_json(response)

    def run(self, question, format_hint):
        # 1. Retrieve docs
        docs = self.retrieval.retrieve(question)
        
        # 2. Generate SQL
        sql = self.generate_sql(question)
        
        # 3. Execute SQL
        sql_result = {}
        if sql:
            sql_result = self.sqlite_tool.execute_query(sql)
            
        # 4. Synthesize
        result = self.synthesize(question, sql_result, docs, format_hint)
        
        return {
            "final_answer": result.get("final_answer"),
            "sql": sql,
            "citations": result.get("citations", []),
            "explanation": "Generated via SimpleAgent"
        }
