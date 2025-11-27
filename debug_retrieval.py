from agent.rag.retrieval import Retrieval

def inspect_context():
    retrieval = Retrieval()
    question = "What is the return policy for unopened beverages?"
    docs = retrieval.retrieve(question)
    
    print(f"Retrieved {len(docs)} docs:")
    for i, doc in enumerate(docs):
        print(f"\n--- Doc {i} ---")
        print(f"ID: {doc.get('id')}")
        print(f"Content: {doc.get('content')}")

if __name__ == "__main__":
    inspect_context()
