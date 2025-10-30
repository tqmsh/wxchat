# Machine Learning Services - McGill GeoAnalysis Assistant

This directory contains the Retrieval Augmented Generation (RAG) system and multi-agent AI services for geospatial data analysis.

- `rag_system/` – Embedding API and vector database for geospatial document retrieval
- `pdf_processor/` – Converts PDFs, text, and geospatial documents to analyzable formats
- `ai_agents/` – Multi-agent reasoning system for complex geospatial analysis

Each service has its own README with setup instructions. After activating a virtual environment you can start the RAG server with:
```bash
cd machine_learning/rag_system
uvicorn app.main:app --reload --port 8002
```

Windows example:
```bat
set PYTHONPATH=machine_learning
python -m uvicorn rag_system.app.main:app --reload --host 0.0.0.0 --port 8002
```

```
machine_learning/
├── rag_system/          # RAG system optimized for geospatial analysis
│   ├── embedding/       # Text embedding for geographic documents
│   ├── services/        # RAG services for spatial data analysis
│   ├── vector_db/       # Supabase vector database
│   ├── llm_clients/     # LLM integration
│   ├── examples/        # Usage examples
│   └── README.md        # Detailed documentation
├── scripts/             # Utility scripts and demos