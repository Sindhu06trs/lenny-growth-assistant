# 🎙️ The Lenny Growth Assistant

> **An AI-powered conversational platform grounded in Lenny’s Podcast transcripts.**  
> Built for Product Managers, Growth Leads, Founders, and Strategy Operators to synthesize product wisdom, draft ~1,250-word Ship 30 for 30 atomic essays, and render live interactive HTML/CSS artifacts.

---

## 📌 Implementation Roadmap & Current Status

| Step | Milestone | Planned Scope | Status |
| :---: | :--- | :--- | :---: |
| **Step 01** | Project Foundation & Documentation | Folder structure, initial configs (.env.example, .gitignore), PRD, architecture, design, README | ✅ **COMPLETE** |
| **Step 01A** | Knowledge-Base Documentation Review | ChatPRD repository verification, agent SDK evaluation, roadmap synchronization | ✅ **COMPLETE** |
| **Step 02** | Frontend Chat Interface & Artifact Viewer | React + Vite + TypeScript + Tailwind layout, Split-Screen Viewer, Tabs (Preview/Code/Split) | ✅ **COMPLETE** |
| **Step 03** | FastAPI Backend Foundation | Core API structure, CORS middleware, Health check, Chat endpoint validation, Pytest suite | ✅ **COMPLETE** |
| **Step 04** | PostgreSQL & pgvector Persistence | Database models (SQLAlchemy), pgvector 0.8.6, Alembic migrations, session/message CRUD | ✅ **COMPLETE** |
| **Step 05** | Implementation Audit | Full inspection of models, routes, database tables, and security posture | ✅ **COMPLETE** |
| **Step 06** | Multi-Provider AI Gateway & Frontend Wiring | Ollama/Claude/OpenAI gateway, provider status API, frontend service & state integration | ✅ **COMPLETE** |
| **Step 07** | Transcript Ingestion & RAG Grounding | ChatPRD loader, chunker, vector similarity search, transcript citations | ✅ **COMPLETE** |
| **Step 08** | Essay & Artifact Generation Pipeline | Ship 30 essay generator, interactive HTML widgets, Markdown strategy guides | ⏳ **NEXT STEP** |
| **Subsequent** | Full Evaluation & Production Deployment | Agent evaluation framework, Docker Compose, production bundling | ⏳ *Planned* |

---

## 📚 Official Knowledge Base & Dataset

The application knowledge base relies on the official open-source archive:
- **Repository URL**: [https://github.com/ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)
- **Episodes Directory**: `episodes/{guest-slug}/transcript.md`
- **Topic Taxonomy**: `index/*.md` (Curated index files for product management, growth, leadership, etc.)

### Episode File Schema (`transcript.md`)
Each episode contains machine-readable **YAML frontmatter** followed by timestamped dialogue turns:

```yaml
# [ILLUSTRATIVE EXAMPLE SCHEMA - NOT RETRIEVED RUNTIME DATA]
---
guest: "Elena Verna"
title: "The ultimate guide to product-led growth (PLG)"
youtube_url: "https://www.youtube.com/watch?v=EXAMPLE_ID"
video_id: "EXAMPLE_ID"
publish_date: "2023-04-16"
description: "Episode summary and show notes..."
duration: "01:14:22"
duration_seconds: 4462
view_count: 52300
channel: "Lenny's Podcast"
---
```

---

## 🤖 AI Agent Framework Evaluation & Selection

The assessment mandates an evaluation of **Anthropic Claude Agent SDK** and **Pi Coding Agent**:

1. **Anthropic Claude Agent SDK**:
   - *Strengths*: Direct integration with Claude 3.5 Sonnet, native tool-use orchestration, prompt caching, structured tool outputs, and conversational context synthesis.
   - *Considerations*: Cloud-centric; for local offline inference (Ollama), a tool-calling bridge is maintained so local models execute the same schemas.
2. **Pi Coding Agent**:
   - *Strengths*: Highly capable for command-line file manipulation and code generation loops.
   - *Considerations*: Tailored for code tasks rather than conversational podcast RAG and essay structuring.
3. **Selected Approach**: Use **Anthropic Claude Agent SDK** as the primary framework for cloud orchestration, paired with a unified tool schema supporting local **Ollama** models in Step 05.

---

## 📁 Repository Structure

```
lenny-growth-assistant/
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git ignore rules for Python, Node, DB & secrets
├── README.md                        # Project overview, setup guide, and roadmap
├── PRD.md                           # Product Requirements Document
├── architecture.md                  # System architecture, DB schema & RAG specs
├── design.md                        # UI/UX design tokens, layout & accessibility
│
├── backend/                         # FastAPI Python Backend (Step 03 Complete)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entrypoint, CORS & error handlers
│   │   ├── core/                    # Core configuration & logging
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Pydantic v2 settings & CORS origin assembler
│   │   │   └── logging_config.py    # Structured logging configuration
│   │   ├── api/                     # REST API Routers
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # Aggregated API router
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── health.py        # GET /health endpoint
│   │   │       └── chat.py          # POST /api/chat validation endpoint
│   │   └── schemas/                 # Pydantic Request & Response Models
│   │       ├── __init__.py
│   │       ├── health.py            # HealthResponse schema
│   │       └── chat.py              # ChatRequest and ChatResponse schemas
│   ├── tests/                       # Pytest Automated Test Suite
│   │   ├── __init__.py
│   │   ├── test_health.py           # Health endpoint tests
│   │   └── test_chat.py             # Chat validation & error handling tests
│   └── requirements.txt             # Backend Python dependencies
│
├── frontend/                        # React + Vite + TypeScript + Tailwind (Step 02 Complete)
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx           # Header with branding and provider status pill
│   │   │   ├── ProviderStatus.tsx   # Model provider indicator with honest status
│   │   │   ├── ChatPane.tsx         # Chat interface, message list, suggested prompts
│   │   │   ├── MessageBubble.tsx    # Message bubbles with role and artifact cards
│   │   │   └── ArtifactViewer.tsx   # 3-tab Artifact Viewer (Preview, Code, Split)
│   │   ├── types/                   # TypeScript interfaces (chat.ts, artifact.ts)
│   │   ├── App.tsx                  # Root state & responsive 2-pane layout
│   │   └── index.css                # Tailwind directives & design system tokens
│   ├── package.json                 # Frontend dependencies & scripts
│   └── vite.config.ts               # Vite server configuration (Port 5173)
│
└── data/                            # Transcript Data Storage
    ├── raw/                         # Raw transcript text / cloned repository
    └── samples/                     # Curated sample transcripts for testing
```

---

## 🛠️ Setup & Execution Guide (Step 06)

### Prerequisites
- **Python**: `3.10+` (Installed in `backend/.venv`)
- **PostgreSQL**: `17.11` with `pgvector 0.8.6` installed
- **Node.js**: `v18+` or `v20+` with npm
- **Ollama** (Optional for local LLM inference): [https://ollama.com](https://ollama.com)

---

### 1. Start PostgreSQL (Windows)
Verify or start the PostgreSQL 17 Windows Service:
```powershell
# Check service status or start PostgreSQL:
net start postgresql-x64-17

# Verify connection using psql:
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d lenny_growth_db -c "\dx"
# Expected output shows vector extension (0.8.6) installed
```

---

### 2. Configure Environment Variables
Copy `.env.example` to `.env` in the project root if not already done:
```powershell
Copy-Item .env.example .env
```
Key configuration parameters:
```dotenv
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lenny_growth_db

# Default LLM Provider (ollama | anthropic | openai)
DEFAULT_LLM_PROVIDER=ollama
LLM_REQUEST_TIMEOUT=60.0

# Ollama Local Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Optional Cloud Providers (Leave empty if not using)
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# Frontend API URL
VITE_API_BASE_URL=http://localhost:8000
```
> **Security Guardrail**: Never commit `.env` or hardcode API keys. The application safely marks unconfigured providers as `unavailable` or `not_configured` without crashing.

---

### 3. Install & Start Ollama (Local AI Provider)
1. Download and install Ollama for Windows from [https://ollama.com/download](https://ollama.com/download).
2. Start the Ollama desktop service (starts automatically in Windows taskbar, serving at `http://localhost:11434`).
3. Download the configured model in PowerShell:
```powershell
ollama pull llama3.1:8b
# Verify installed models:
ollama list
```
If Ollama is not running, the application gracefully flags Ollama as `unavailable` without blocking the backend or frontend.

---

### 4. Start the FastAPI Backend
```powershell
cd "c:\Users\Sindhuja Ramaraj\OneDrive\Documents\lenny-growth-assistant\backend"

# Run with the dedicated virtual environment:
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Base URL**: `http://127.0.0.1:8000`
* **Health Check**: `http://127.0.0.1:8000/health`
* **Database Readiness**: `http://127.0.0.1:8000/health/db`
* **Provider Status**: `http://127.0.0.1:8000/api/providers/status`
* **Interactive Docs**: `http://127.0.0.1:8000/docs`

---

### 5. Start the React Frontend
```powershell
cd "c:\Users\Sindhuja Ramaraj\OneDrive\Documents\lenny-growth-assistant\frontend"

# Launch Vite development server:
npm.cmd run dev
```
* **Frontend UI**: `http://localhost:5173`

---

### 6. Transcript Ingestion & pgvector RAG Pipeline (Step 07)

#### Source Repository
Transcripts are sourced from the official community repository:  
**`https://github.com/ChatPRD/lennys-podcast-transcripts`**

To download the full transcript archive:
```powershell
# Clone the repository into data/raw:
git clone https://github.com/ChatPRD/lennys-podcast-transcripts data/raw
```
*Curated sample episodes (e.g. Brian Chesky, Shreyas Doshi) are also included in `data/samples/` for immediate local execution and testing.*

#### Supported File Formats
1. **Markdown (`.md`)**: Full transcripts with YAML frontmatter metadata (`guest`, `title`, `youtube_url`, `video_id`, `publish_date`, `duration_seconds`) and speaker/timestamp turns (e.g., `Brian Chesky (00:00:00):`).
2. **Text (`.txt`)**: Plain-text transcript dialogues with timestamps.
3. **JSON (`.json`)**: Structured export documents with metadata and utterances.

#### Embedding Provider Configuration & Vector Dimensions
- **Schema Specification**: PostgreSQL `transcript_chunks.embedding` column is configured for `Vector(1536)` (optimized for OpenAI `text-embedding-3-small`).
- **OpenAI Embeddings**:
  - Model: `text-embedding-3-small` (1536 dimensions)
  - Requires: `OPENAI_API_KEY` in `.env`
- **Ollama Local Embeddings**:
  - Model: `nomic-embed-text` (768 dimensions)
  - *Dimension Notice*: The pipeline includes automated dimension validation. If a 768-dimensional model is used against the 1536-dimensional column, the pipeline safely warns about the dimension difference and allows text-only ingestion without corrupting the database.

#### Windows Ingestion CLI Commands
Run the ingestion CLI from the `backend/` directory:
```powershell
cd "c:\Users\Sindhuja Ramaraj\OneDrive\Documents\lenny-growth-assistant\backend"

# 1. Ingest sample transcripts without embeddings (text & metadata only):
.\.venv\Scripts\python.exe -m app.ingestion.cli --source ..\data\samples --no-embed

# 2. Ingest sample transcripts with dense embeddings (OpenAI 1536 dims):
.\.venv\Scripts\python.exe -m app.ingestion.cli --source ..\data\samples --provider openai

# 3. Ingest the full cloned repository from data/raw:
.\.venv\Scripts\python.exe -m app.ingestion.cli --source ..\data\raw

# 4. Verify ingested database counts & statistics:
.\.venv\Scripts\python.exe -m app.ingestion.cli --verify
```

---

### 7. Run Automated Tests
```powershell
# Backend Pytest Suite (50 tests covering ingestion, embeddings, retrieval, RAG, providers, database):
cd "c:\Users\Sindhuja Ramaraj\OneDrive\Documents\lenny-growth-assistant\backend"
.\.venv\Scripts\python.exe -m pytest tests -v

# Frontend Automated Tests:
cd "c:\Users\Sindhuja Ramaraj\OneDrive\Documents\lenny-growth-assistant\frontend"
npm.cmd test

# Frontend TypeScript Validation & Production Build:
npm.cmd run build
```

---

## 🔌 API Endpoints Implemented

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Core application health status (`200 OK`) |
| `/health/db` | `GET` | PostgreSQL & pgvector connectivity check |
| `/api/providers/status` | `GET` | Multi-provider connection & configuration status (safe, no secrets) |
| `/api/chat` | `POST` | RAG inference gateway: vector query embedding, pgvector retrieval, prompt grounding, citation generation & turn persistence |
| `/api/sessions` | `GET` | List all conversation sessions (`updated_at DESC`) |
| `/api/sessions` | `POST` | Create a new isolated chat session |
| `/api/sessions/{session_id}/messages` | `GET` | Retrieve chronological message history for a session |
| `/api/sessions/{session_id}` | `DELETE` | Delete session and cascade delete all associated messages |

---

## ⚠️ Known Limitations & Guardrails
* **Genuine Citations Only**: The chat endpoint returns citations only when verified transcript chunks are retrieved from the database. It never fabricates citations (`sources: []` when ungrounded).
* **Clear Distinction**: The assistant is instructed to distinguish between facts directly quoted from Lenny's guests and general product management advice.
* **Empty Database Transparency**: If no transcript chunks are indexed, the application clearly informs the user that transcripts have not yet been ingested and gives the exact CLI command to ingest them.
* **Artifact Generation Pending**: Interactive HTML artifacts, Markdown strategy guides, and Ship 30 essays are scheduled for **Step 08**.

---

## 🗺️ Recommended Next Step

**Step 08: Essay & Artifact Generation Pipeline**
- Implement structured Ship 30 essay generation (hook, body paragraphs, takeaways, ~1250 words).
- Implement interactive HTML widgets and Markdown strategy documents in the 3-tab Artifact Viewer (`Preview`, `Code`, `Split`).
- Add artifact persistence and versioning.
