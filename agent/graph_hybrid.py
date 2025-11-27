import dspy
from typing import TypedDict, Annotated, List, Dict, Any, Union
from langgraph.graph import StateGraph, END
from agent.dspy_signatures import Router, GenerateSQL, SynthesizeAnswer, ExtractConstraints, RepairSQL
from agent.tools.sqlite_tool import SQLiteTool
from agent.rag.retrieval import Retrieval
import json

# Define the state
class AgentState(TypedDict):
    question: str
    format_hint: str
    tool_choice: str
    retrieved_docs: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    sql_query: str
    sql_result: Dict[str, Any]
    final_answer: Any
    citations: List[str]
    explanation: str
    repair_count: int
    error: str

class HybridAgent:
    def __init__(self):
        self.sqlite_tool = SQLiteTool()
        self.retrieval = Retrieval()
        self.schema = self.sqlite_tool.get_schema()
        
        # DSPy Modules
        self.router = dspy.ChainOfThought(Router)
        self.planner = dspy.ChainOfThought(ExtractConstraints)
        self.sql_generator = dspy.ChainOfThought(GenerateSQL)
        self.synthesizer = dspy.ChainOfThought(SynthesizeAnswer)
        self.sql_repairer = dspy.ChainOfThought(RepairSQL)
        
    def router_node(self, state: AgentState) -> AgentState:
        pred = self.router(question=state["question"])
        return {"tool_choice": pred.tool.lower()}

    def retriever_node(self, state: AgentState) -> AgentState:
        docs = self.retrieval.retrieve(state["question"])
        return {"retrieved_docs": docs}

    def planner_node(self, state: AgentState) -> AgentState:
        docs_str = json.dumps(state["retrieved_docs"], indent=2)
        pred = self.planner(question=state["question"], retrieved_docs=docs_str)
        constraints = {
            "date_range": pred.date_range,
            "kpi_formula": pred.kpi_formula,
            "category_mapping": pred.category_mapping
        }
        return {"constraints": constraints}

    def sql_generator_node(self, state: AgentState) -> AgentState:
        # Simplified call - removed constraints to reduce noise
        try:
            pred = self.sql_generator(
                question=state["question"],
                db_schema=self.schema
            )
            # Clean SQL: remove markdown code blocks if present
            sql = pred.sql_query.replace("```sql", "").replace("```", "").strip()
        except:
            sql = "" # Fallback if generation fails
            
        return {"sql_query": sql}

    def executor_node(self, state: AgentState) -> AgentState:
        result = self.sqlite_tool.execute_query(state["sql_query"])
        if result["error"]:
            return {"sql_result": result, "error": result["error"]}
        return {"sql_result": result, "error": ""}

    def synthesizer_node(self, state: AgentState) -> AgentState:
        docs_str = json.dumps(state["retrieved_docs"], indent=2)
        sql_result_str = json.dumps(state["sql_result"], indent=2)
        
        # Add helpful context about the SQL result structure
        if state["sql_result"].get("rows") and len(state["sql_result"]["rows"]) > 0:
            sql_result_str = f"SQL Results (extract actual values from 'rows'):\n{sql_result_str}"
        elif state["sql_result"].get("error"):
            sql_result_str = f"SQL Error: {state['sql_result']['error']}\nUse retrieved_docs to answer."
        
        pred = self.synthesizer(
            question=state["question"],
            format_hint=state["format_hint"],
            sql_query=state["sql_query"],
            sql_result=sql_result_str,
            retrieved_docs=docs_str
        )
        
        # Robust parsing for final_answer
        final_answer = pred.final_answer
        explanation = "" # Rationale removed from signature
        
        # Try to ensure final_answer is the correct type if it's a string looking like JSON
        if isinstance(final_answer, str):
            try:
                # Attempt to parse if it looks like a dict or list
                if final_answer.strip().startswith("{") or final_answer.strip().startswith("["):
                    final_answer = json.loads(final_answer)
            except:
                pass

        # Parse citations
        try:
            citations = pred.citations
            if isinstance(citations, str):
                citations = [c.strip() for c in citations.split(",")]
        except:
            citations = []

        return {
            "final_answer": final_answer,
            "citations": citations,
            "explanation": explanation
        }

    def repair_node(self, state: AgentState) -> AgentState:
        """Use RepairSQL to fix the query based on the error message."""
        try:
            pred = self.sql_repairer(
                original_query=state["sql_query"],
                error_message=state["error"],
                db_schema=self.schema
            )
            # Clean the fixed SQL
            fixed_sql = pred.fixed_query.replace("```sql", "").replace("```", "").strip()
            return {
                "sql_query": fixed_sql,
                "repair_count": state["repair_count"] + 1,
                "error": ""  # Clear error after repair
            }
        except Exception as e:
            # If repair fails, just increment count and keep original query
            return {"repair_count": state["repair_count"] + 1}

    def build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("router", self.router_node)
        workflow.add_node("retriever", self.retriever_node)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("sql_generator", self.sql_generator_node)
        workflow.add_node("executor", self.executor_node)
        workflow.add_node("synthesizer", self.synthesizer_node)
        workflow.add_node("repair", self.repair_node)
        
        workflow.set_entry_point("router")
        
        workflow.add_edge("router", "retriever")
        workflow.add_edge("retriever", "planner")
        
        def route_after_planner(state):
            if state["tool_choice"] == "rag":
                return "synthesizer"
            return "sql_generator"

        workflow.add_conditional_edges(
            "planner",
            route_after_planner,
            {
                "synthesizer": "synthesizer",
                "sql_generator": "sql_generator"
            }
        )
        
        workflow.add_edge("sql_generator", "executor")
        
        def route_after_executor(state):
            if state["error"] and state["repair_count"] < 2:
                return "repair"
            return "synthesizer"
            
        workflow.add_conditional_edges(
            "executor",
            route_after_executor,
            {
                "repair": "repair",
                "synthesizer": "synthesizer"
            }
        )
        
        workflow.add_edge("repair", "sql_generator") # Assume repair fixes SQL
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
