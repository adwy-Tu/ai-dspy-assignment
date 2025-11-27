# Retail Analytics Copilot

A local, free AI agent that answers retail analytics questions using RAG over local docs and SQL over a local SQLite DB (Northwind).

## Graph Design
The agent uses a LangGraph with the following nodes:
- **Router**: Decides whether to use RAG, SQL, or a Hybrid approach.
- **Retriever**: Fetches relevant chunks from local markdown documents using TF-IDF.
- **Planner**: Extracts constraints (dates, KPIs) from retrieved docs.
- **SQL Generator**: Generates SQLite queries based on the question and schema.
- **Executor**: Executes the SQL queries against the Northwind database.
- **Synthesizer**: Combines SQL results and retrieved docs to produce a typed answer with citations.
- **Repair**: A loop that attempts to fix SQL errors or format issues (up to 2 times).

## DSPy Optimization
I chose to optimize the **Router** module using `BootstrapFewShot`.
- **Goal**: Improve the accuracy of selecting the correct tool (RAG vs SQL vs Hybrid).
- **Metric**: Exact match of the predicted tool against a small labeled dataset.
- **Result**: The router learns from examples to better distinguish between questions requiring DB access, doc access, or both.

## Assumptions & Trade-offs
- **CostOfGoods**: Approximated as `0.7 * UnitPrice` where missing, as per instructions.
- **Local Execution**: Uses `phi3.5:3.8b-mini-instruct-q4_K_M` via Ollama for all inference.
- **Retrieval**: Uses simple TF-IDF on paragraph-level chunks.
- **SQL**: Uses views (`orders`, `order_items`, `products`, `customers`) for simplified querying.

## How to Run
1. Ensure Ollama is running: `ollama serve`
2. Pull the model: `ollama pull phi3.5:3.8b-mini-instruct-q4_K_M`
3. Run the agent:
   ```bash
   python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out outputs_hybrid.jsonl
   ```
