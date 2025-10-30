# McGill GeoAnalysis Assistant

**A McGill University research project for geospatial data analysis powered by AI agents and RAG systems.**

This is the **McGill GeoAnalysis Assistant** repo — a multi-agent AI system designed to help researchers analyze geospatial data, understand geographic patterns, and extract insights from spatial documents. This project is part of McGill University's geospatial research initiative under Professor Renee Sieber.

The system combines advanced RAG (Retrieval-Augmented Generation) capabilities with a multi-agent workflow to provide intelligent analysis of geospatial data including maps, spatial statistics, and geographic information systems (GIS) data.

## Repository Layout

- `frontend/` – React application built with Vite and TailwindCSS for the web interface
- `backend/` – FastAPI service exposing chat, file processing, and analysis APIs
- `machine_learning/` – Embedding and RAG services, plus multi-agent system for complex analysis

## Key Features

- **Multi-Agent System**: Strategic analysis using multiple specialized AI agents
- **RAG-Powered**: Context-aware responses from uploaded geospatial documents
- **Geospatial Analysis**: Specialized for geographic data and spatial analysis
- **Document Processing**: Support for PDF, text, LaTeX, and geospatial data formats
- **Real-time Chat**: Interactive interface for exploring geospatial concepts

## Quick Start

1. **Install dependencies**

On macOS/Linux you can run the helper script:
```bash
./setup.sh
```

Remember to run `chmod +x setup.sh` before executing it.

```bash
./setup.sh          # setup + run everything (default)
./setup.sh setup    # setup only
./setup.sh start    # run services
./setup.sh stop     # stop services
./setup.sh status   # status
```

Or install manually:
```bash
pip install -r backend/requirements.txt
pip install -r machine_learning/pdf_processor/requirements.txt
pip install -r machine_learning/rag_system/requirements.txt -c constraints.txt --upgrade --upgrade-strategy eager
pip install -r machine_learning/ai_agents/requirements.txt
```

Windows users should follow `windows_proj_env_setup.md`.

2. **Environment files** – copy the provided examples to `.env` inside `backend/` and `machine_learning/rag_system/` and update credentials.

3. **Run services**
   ```bash
   # Backend
   PYTHONPATH=backend python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

   # Frontend (in a new terminal)
   cd frontend && npm run dev

   # RAG System (in a new terminal)
   PYTHONPATH=machine_learning/rag_system python -m rag_system.main

   # Multi-Agent System (in a new terminal, optional)
   PYTHONPATH=machine_learning/ai_agents python -m ai_agents.main
   ```

4. Open http://localhost:5173 to access the GeoAnalysis Assistant.

## Architecture

The system uses a multi-agent architecture with:
- **Retrieve Agent**: Finds relevant information from documents
- **Strategist Agent**: Develops analysis strategies
- **Critic Agent**: Evaluates analytical approaches
- **Moderator Agent**: Coordinates the analysis process
- **Reporter Agent**: Synthesizes final results

## Development

This project is developed in collaboration with McGill University's Geography department and CEIMIA. We focus on creating impactful systems for geospatial data analysis while publishing academic research on multi-agent AI systems.

## License

© 2025 McGill University. All rights reserved.