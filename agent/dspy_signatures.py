import dspy
from typing import List, Optional

class Router(dspy.Signature):
    """Decide whether to use RAG, SQL, or Hybrid approach to answer the question."""
    
    question = dspy.InputField(desc="The user's question about retail analytics.")
    rationale = dspy.OutputField(desc="Reasoning for the chosen tool.")
    tool = dspy.OutputField(desc="One of: 'rag', 'sql', 'hybrid'.")

class GenerateSQL(dspy.Signature):
    """Generate a SQLite query for the given question and schema.
    
    Schema:
    - Tables: Categories, Customers, Employees, OrderDetails, Orders, Products, Shippers, Suppliers, Territories, Region
    - Views: Alphabetical list of products, Order Subtotals, Product Sales for 1997, Category Sales for 1997, Sales by Category
    
    Rules:
    1. Use ONLY SQLite syntax (strftime, COALESCE).
    2. Use ONLY the tables/views listed above.
    3. Return ONLY the SQL query in the sql_query field.
    """
    
    question = dspy.InputField(desc="The user's question.")
    db_schema = dspy.InputField(desc="The database schema.")
    sql_query = dspy.OutputField(desc="The SQLite query.")

class SynthesizeAnswer(dspy.Signature):
    """Synthesize a final answer based on the question, SQL results, and retrieved documents.
    
    Output MUST be a valid JSON object with 'final_answer' and 'citations' fields.
    
    Format Rules:
    - "int" -> final_answer: 14
    - "float" -> final_answer: 123.45
    - "{category:str, quantity:int}" -> final_answer: {"category": "Beverages", "quantity": 542}
    - "list[{product:str, revenue:float}]" -> final_answer: [{"product": "A", "revenue": 10.5}, ...]
    
    If SQL failed, use retrieved_docs. If no answer found, return null.
    """
    
    question = dspy.InputField(desc="The user's question.")
    format_hint = dspy.InputField(desc="The expected format of the answer.")
    sql_query = dspy.InputField(desc="The executed SQL query.")
    sql_result = dspy.InputField(desc="The result of the SQL query.")
    retrieved_docs = dspy.InputField(desc="Relevant document chunks.")
    
    final_answer = dspy.OutputField(desc="The final answer matching format_hint EXACTLY.")
    citations = dspy.OutputField(desc="List of citations.")

class ExtractConstraints(dspy.Signature):
    """Extract constraints from the question and retrieved documents to help with SQL generation."""
    
    question = dspy.InputField(desc="The user's question.")
    retrieved_docs = dspy.InputField(desc="Relevant document chunks.")
    
    date_range = dspy.OutputField(desc="Date range mentioned or implied (start, end) in YYYY-MM-DD format.")
    kpi_formula = dspy.OutputField(desc="KPI formula or definition to use.")
    category_mapping = dspy.OutputField(desc="Mapping of product categories if relevant.")

class RepairSQL(dspy.Signature):
    """Fix a SQLite query that produced an error.
    
    Common fixes:
    - Replace EXTRACT(YEAR FROM col) with strftime('%Y', col)
    - Replace DATE_PART('month', col) with strftime('%m', col)
    - Replace IFNULL(x, y) with COALESCE(x, y)
    - Fix table/column name typos against schema
    - Remove invalid syntax like BETWEEN=/Users/...
    """
    
    original_query = dspy.InputField(desc="The SQL query that failed.")
    error_message = dspy.InputField(desc="The error message from SQLite.")
    db_schema = dspy.InputField(desc="The database schema for reference.")
    
    reasoning = dspy.OutputField(desc="Explanation of what was wrong and how to fix it.")
    fixed_query = dspy.OutputField(desc="The corrected SQLite query.")
