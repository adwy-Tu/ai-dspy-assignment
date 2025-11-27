import argparse
import json
import dspy
import os
from agent.graph_hybrid import HybridAgent

def main():
    parser = argparse.ArgumentParser(description="Retail Analytics Copilot")
    parser.add_argument("--batch", required=True, help="Path to input JSONL file")
    parser.add_argument("--out", required=True, help="Path to output JSONL file")
    args = parser.parse_args()

    # Use SimpleAgent instead of HybridAgent
    from agent.simple_agent import SimpleAgent
    agent = SimpleAgent()
    
    # Clear output file first
    with open(args.out, "w") as f:
        pass

    with open(args.batch, "r") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            
            print(f"Processing: {item['id']}")
            
            try:
                # Run the simple agent
                result = agent.run(item["question"], item["format_hint"])
                
                output = {
                    "id": item["id"],
                    "final_answer": result.get("final_answer"),
                    "sql": result.get("sql", ""),
                    "confidence": 1.0 if result.get("final_answer") else 0.0,
                    "explanation": result.get("explanation", ""),
                    "citations": result.get("citations", [])
                }
            except Exception as e:
                print(f"Error processing {item['id']}: {e}")
                output = {
                    "id": item["id"],
                    "final_answer": None,
                    "sql": "",
                    "confidence": 0.0,
                    "explanation": f"Error: {str(e)}",
                    "citations": []
                }
            
            # Write incrementally
            with open(args.out, "a") as out_f:
                out_f.write(json.dumps(output) + "\n")
                out_f.flush()

    print(f"Results written to {args.out}")

if __name__ == "__main__":
    main()
