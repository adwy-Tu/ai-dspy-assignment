import dspy
from dspy.teleprompt import BootstrapFewShot
from agent.dspy_signatures import Router
from agent.graph_hybrid import HybridAgent

def optimize_router():
    # Define a small training set for the router
    train_examples = [
        dspy.Example(question="What is the return policy for unopened beverages?", tool="rag").with_inputs("question"),
        dspy.Example(question="How many orders were placed in 1997?", tool="sql").with_inputs("question"),
        dspy.Example(question="What was the total revenue for Beverages in Summer 1997?", tool="hybrid").with_inputs("question"),
        dspy.Example(question="List the top 5 products by unit price.", tool="sql").with_inputs("question"),
        dspy.Example(question="Who is the contact person for Alfreds Futterkiste?", tool="sql").with_inputs("question"),
        dspy.Example(question="What are the KPI definitions for Gross Margin?", tool="rag").with_inputs("question"),
        dspy.Example(question="Calculate the average order value for Winter Classics 1997.", tool="hybrid").with_inputs("question"),
        dspy.Example(question="Show me the marketing calendar for 1997.", tool="rag").with_inputs("question"),
        dspy.Example(question="Which supplier provides Exotic Liquids?", tool="sql").with_inputs("question"),
        dspy.Example(question="What is the return window for produce?", tool="rag").with_inputs("question"),
    ]

    # Define a metric for the router
    def router_metric(example, pred, trace=None):
        return example.tool.lower() == pred.tool.lower()

    # Configure the optimizer
    config = dict(max_bootstrapped_demos=3, max_labeled_demos=3)
    teleprompter = BootstrapFewShot(metric=router_metric, **config)

    # Compile the router
    print("Compiling Router...")
    compiled_router = teleprompter.compile(dspy.ChainOfThought(Router), trainset=train_examples)
    
    print("Optimization complete.")
    return compiled_router

if __name__ == "__main__":
    # Configure DSPy (needs to match main config)
    lm = dspy.LM(model='ollama/phi3.5:3.8b-mini-instruct-q4_K_M', api_base='http://localhost:11434')
    dspy.settings.configure(lm=lm)
    
    optimized_router = optimize_router()
    
    # Save the optimized module (optional, or just print success)
    print("Router optimized successfully.")
