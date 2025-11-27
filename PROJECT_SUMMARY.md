# Retail Analytics Copilot - Project Summary

## Overview
A hybrid RAG + SQL agent for answering business questions about the Northwind retail database using natural language.

## Final Architecture

### Components
1. **SimpleAgent** (`agent/simple_agent.py`): Main agent using direct Ollama API calls
2. **SQLite Tool** (`agent/tools/sqlite_tool.py`): Database interaction
3. **RAG Retrieval** (`agent/rag/retrieval.py`): Document-based context retrieval
4. **Runner** (`run_agent_hybrid.py`): CLI interface for batch processing

### Model
- **Recommended**: `llama3.2:3b` (67% accuracy)
- **Alternative**: `phi3.5:3.8b` (33% accuracy)

## Quick Start

### Prerequisites
```bash
# Install Ollama
# Download from: https://ollama.ai

# Pull the model
ollama pull llama3.2:3b
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_db.py
```

### Usage
```bash
# Run on sample questions
python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out results.jsonl

# Run on single question
python -c "from agent.simple_agent import SimpleAgent; agent = SimpleAgent(); print(agent.run('What is the return policy for beverages?', 'int'))"
```

## Project Evolution

### Phase 1: Initial Setup (DSPy)
- Used DSPy framework with complex signatures
- **Result**: Model hallucinations and gibberish output

### Phase 2: Simplified Architecture
- Replaced DSPy with direct API calls
- Added SQL validation and cleaning
- **Result**: Eliminated hallucinations, but SQL quality still poor

### Phase 3: Model Comparison
- Tested phi3.5 with enhanced prompts
- Tested llama3.2:3b
- **Result**: llama3.2 achieved 2x improvement (67% vs 33%)

## Key Features

### SQL Generation
- Few-shot prompting with examples
- Automatic dialect conversion (YEAR → strftime)
- Validation to reject incomplete queries

### Answer Synthesis
- Separate prompts for SQL vs document-based answers
- Robust JSON parsing with regex fallback
- Format-aware output (int, float, dict, list)

### Error Handling
- SQL validation before execution
- Graceful fallback to documents when SQL fails
- Detailed error logging

## Performance

| Metric | Value |
|--------|-------|
| Accuracy | 67% (4/6 questions) |
| Avg Time/Question | ~30 seconds |
| Model Size | 2.0 GB |
| Memory Usage | ~4 GB RAM |

## Known Limitations

1. **Missing Table Aliases**: Occasionally references columns without proper JOIN
2. **Complex Calculations**: Margin/KPI calculations may need manual verification
3. **Date Handling**: Some edge cases with date range queries

## Troubleshooting

### Model outputs gibberish
- **Solution**: Ensure using llama3.2:3b, not phi3.5

### SQL syntax errors
- **Check**: Validation is enabled in `simple_agent.py`
- **Fix**: Add more examples to few-shot prompt

### Slow performance
- **Cause**: Model inference time
- **Options**: Use smaller model or GPU acceleration

## Files Structure

```
.
├── agent/
│   ├── simple_agent.py          # Main agent (llama3.2)
│   ├── simple_agent_llama.py    # Backup llama version
│   ├── tools/
│   │   └── sqlite_tool.py       # Database interface
│   └── rag/
│       └── retrieval.py         # Document retrieval
├── docs/                        # Business documents
├── run_agent_hybrid.py          # CLI runner
├── sample_questions_hybrid_eval.jsonl  # Test questions
└── northwind.db                 # SQLite database
```

## Next Steps

1. Add automatic JOIN detection
2. Implement SQL repair for missing aliases
3. Fine-tune prompts for KPI calculations
4. Add caching for repeated queries

## Credits

Built using:
- Ollama (LLM inference)
- SQLite (Database)
- ChromaDB (Vector store)
- Sentence Transformers (Embeddings)
