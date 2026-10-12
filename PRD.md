# Product Requirements Document (PRD)
## The Lenny Growth Assistant

**Version:** 1.2.0 (Knowledge-Base & Roadmap Synchronization)  
**Author:** Forward Deployed Engineering Assessment Candidate  
**Status:** In Planning / Design Phase  
**Last Updated:** October 2026

---

## 1. Executive Summary

**The Lenny Growth Assistant** is an intelligent, full-stack conversational application designed to unlock the insights within **Lenny’s Podcast** transcripts. It empowers Product Managers (PMs), Growth Leaders, Founders, and Strategy Operators to query, synthesize, and transform product wisdom into actionable frameworks, atomic essays, and interactive artifacts.

### Key Capabilities (Planned):
1. **Grounded Answers with Citations**: Responses are strictly grounded in authentic transcripts sourced from the official [ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) repository with traceable citations (guest name, episode title, YouTube link with timestamp, and excerpt).
2. **Independent Chat Sessions**: Maintains persistent conversation sessions with follow-up memory.
3. **"Ship 30 for 30" Style Essays**: Generates ~1,250-word atomic essays featuring punchy hooks, single core thesis, structured sub-points, and tactical playbooks.
4. **Interactive Artifacts**: Generates rich Markdown documents and live HTML/CSS widgets (e.g., retention calculators, prioritization matrices).
5. **Split-Screen Artifact Viewer**: Displays generated artifacts in a dedicated side-by-side viewer beside the chat.
6. **Dual Model Execution**: Supports Local LLM (Ollama) and Cloud LLM (Anthropic Claude / OpenAI) with a live provider health indicator.

---

## 2. Official Data Source & Knowledge Base Structure

The knowledge base relies exclusively on the official open-source archive:
- **Repository URL**: `https://github.com/ChatPRD/lennys-podcast-transcripts`
- **Dataset Scope**: Transcript archive of *Lenny’s Podcast* featuring 200+ product and growth interviews.

### 2.1 Repository Layout
Based on the repository documentation, the files are structured as follows:

```
lennys-podcast-transcripts/
├── episodes/
│   └── {guest-slug}/                # Subdirectory per guest (e.g., 'elena-verna', 'shreyas-doshi')
│       └── transcript.md            # Markdown transcript with YAML frontmatter
├── index/
│   ├── README.md                    # Topic taxonomy directory
│   ├── product-management.md        # Curated index of episodes for Product Management
│   ├── growth.md                    # Curated index of episodes for Growth & Metrics
│   ├── leadership.md                # Curated index of episodes for Leadership & Hiring
│   └── ...                          # Additional category indexes
└── scripts/                         # Helper and index generation scripts
```

### 2.2 Episode Metadata Schema (`transcript.md`)
*(Note: The following block is an illustrative schema example showing expected YAML fields; actual metadata is parsed dynamically at runtime).*

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

The body of each `transcript.md` contains timestamped dialogue turns between Lenny and the guest.

---

## 3. Target Personas & User Workflows (Illustrative)

*(Note: The queries below are illustrative user scenarios representing planned system workflows).*

| Persona | Primary Goal | Illustrative Scenario |
| :--- | :--- | :--- |
| **Product Manager (B2B SaaS)** | PLG vs. Sales-Led conversion tactics | *Querying advice on freemium triggers and self-serve monetization.* |
| **Growth Lead (Marketplace)** | Bootstrapping supply/demand liquidity | *Querying two-sided marketplace launch playbooks and tactical checklists.* |
| **Founder / Operator** | Thought leadership & atomic essays | *Requesting a ~1,250-word Ship 30 for 30 essay on viral loops vs. funnels.* |
| **Design / Strategy Lead** | Interactive tooling for planning | *Generating an interactive HTML/CSS ROI calculator based on benchmarks.* |

---

## 4. Core Functional Requirements & Knowledge-Base Criteria

### 4.1 Knowledge Base Ingestion & Grounding Requirements (Planned for Step 06)
- **FR-KB-1 (Source Ingestion)**: Ingest transcripts from `https://github.com/ChatPRD/lennys-podcast-transcripts`. Extract all YAML frontmatter attributes (`guest`, `title`, `youtube_url`, `video_id`, `publish_date`, `description`, `duration_seconds`) and store them with the transcript record.
- **FR-KB-2 (Semantic & Speaker Turn Chunking)**: Segment transcripts into 500–800 token chunks with 100-token overlap, preserving speaker boundaries and timestamp markers (e.g. `[00:14:23]`).
- **FR-KB-3 (Hybrid Retrieval)**: Execute dual retrieval combining dense vector similarity (`pgvector`) and sparse keyword matching (PostgreSQL `tsvector` BM25) fused via Reciprocal Rank Fusion (RRF).
- **FR-KB-4 (Incremental Sync & Refresh)**: Support incremental synchronization by tracking file SHA256 hashes to re-index only new or modified `transcript.md` files without wiping existing history.
- **FR-KB-5 (Complete Traceability)**: Every generated citation must map back to:
  1. Episode Title & Guest Name
  2. Original Repository Path (`episodes/{guest-slug}/transcript.md`)
  3. YouTube Video URL with exact timestamp link (`youtube_url&t=X`)
  4. Exact transcript excerpt quotation
  5. Chunk Identifier in PostgreSQL

### 4.2 Hallucination Prevention & Knowledge Boundaries (Planned for Step 07)
- **FR-KB-6 (Uncertainty & Refusal Acknowledgment)**: When the retrieved transcript segments do not contain sufficient evidence to answer a query (or similarity falls below threshold `0.70`), the agent must **explicitly state** that Lenny's transcripts do not cover the topic. It must never fabricate quotes, invent fake episode titles, or substitute ungrounded external claims as transcript facts.

### 4.3 Multi-Session Chat & Contextual Memory (Planned for Steps 02–04)
- **FR-CS-1**: Independent chat sessions with persistent context, drill-down follow-up questions, and session switching.
- **FR-CS-2**: Session history stored in PostgreSQL and accessible across application restarts.

### 4.4 "Ship 30 for 30" Style Essay Generator (Planned for Subsequent Steps)
- **FR-ES-1**: Generate structured ~1,250-word atomic essays:
  - **Hook & Headline**: 1 compelling problem-oriented hook.
  - **Single Strong Thesis**: 1 core contrarian insight or framework.
  - **3–5 Structured Sub-Points**: Bold lead-ins, bulleted takeaways, guest case studies.
  - **Tactical Action Plan**: Concrete steps cited from transcripts.
  - **Punchy Conclusion**: Synthesis and memorable takeaway.
- **FR-ES-2**: Live word count validator and reading time indicator.

### 4.5 Dynamic Multi-Format Artifacts & Split Viewer (Planned for Steps 02 & Subsequent Steps)
- **FR-AR-1**: Multi-format generation: Structured Markdown, executable HTML/CSS/JS widgets, and Ship 30 essays.
- **FR-AR-2**: Dedicated 2-pane Split Viewer with Preview, Code, and Split viewing tabs.
- **FR-AR-3**: Secure sandboxed rendering inside `<iframe sandbox="allow-scripts" />` with `srcdoc`.
- **FR-AR-4**: Export actions: Copy to clipboard, download file (`.html`, `.md`), and fullscreen mode.

### 4.6 Dual Model Provider Support (Planned for Step 05)
- **FR-LLM-1**: Support Local Models (Ollama: Llama 3.1, Nomic Embed) and Cloud Models (Anthropic Claude 3.5 Sonnet, OpenAI GPT-4o).
- **FR-LLM-2**: Real-time Provider Indicator Pill in header displaying model name, latency, and connection status.

---

## 5. End-to-End Planned Retrieval & Agent Workflow

```mermaid
flowchart TD
    A[User Enters Query] --> B[Generate Query Vector & Sparse Keywords (Planned)]
    B --> C[Execute Hybrid Search in PostgreSQL + pgvector (Planned)]
    C --> D{Retrieval Confidence >= Threshold? (Planned)}
    
    D -->|Yes: Grounded Segments Found| E[Assemble Prompt Context with Citations & Metadata]
    E --> F[Agent Reasoning via Anthropic Claude Agent SDK / Ollama]
    F -->|Answer Synthesis| G[Stream Tokens with Clickable Citation Pills]
    F -->|Artifact Request| H[Emit Artifact to Sandboxed Split Viewer]
    
    D -->|No: Out of Scope / Missing Data| I[Acknowledge Lack of Transcript Coverage Explicitly]
    I --> J[Display Clear Refusal & Suggest Related Known Topics]
```

---

## 6. Implementation Roadmap & Acceptance Checklist

| Step ID | Implementation Phase | Target Scope | Status |
| :--- | :--- | :--- | :---: |
| **Step 01** | Project Foundation & Documentation | Folder structure, PRD, architecture, design, README, .env.example, .gitignore | ✅ **COMPLETE** |
| **Step 01A** | Knowledge-Base Documentation Review | ChatPRD repository verification, agent SDK evaluation, roadmap consistency | ✅ **COMPLETE** |
| **Step 02** | Frontend Chat Interface & Artifact Viewer | React + Vite + TypeScript + Tailwind layout, Split-Screen Viewer, Tabs | ✅ **COMPLETE** |
| **Step 03** | FastAPI Backend Foundation | Core API structure, CORS, routing, Pytest suite | ✅ **COMPLETE** |
| **Step 04** | PostgreSQL Persistence & Database Models | SQLAlchemy models (pgvector), Alembic migrations, session/message CRUD | ✅ **COMPLETE** |
| **Step 05** | Ollama & Cloud-Provider Configuration | Multi-provider connection setup, provider indicator status | ⏳ **NEXT STEP** |
| **Step 06** | Transcript Ingestion & Retrieval | ChatPRD loader, YAML frontmatter parser, chunker, `pgvector` hybrid search | ⏳ *Planned* |
| **Step 07** | Agent Integration & Grounded Answers | Anthropic Claude Agent SDK / Ollama tool integration, citation pills, refusal rules | ⏳ *Planned* |
| **Subsequent** | Essays, Artifacts, Testing & Deployment | Ship 30 essay generator, iframe sandboxing, unit/E2E tests, Docker Compose | ⏳ *Planned* |

---

## 7. Non-Functional Requirements & Guardrails

1. **Transcript Truth Priority**: Grounded transcript truth supersedes model pre-trained assumptions.
2. **Zero Fabrication Policy**: Never fabricate citations, quotes, guest names, or fake URLs.
3. **Security & Sandboxing**: All user-generated or AI-generated HTML/CSS/JS artifacts must be rendered inside a secure `iframe` with `sandbox="allow-scripts"`.
4. **Sub-second Perceived Latency**: Chat responses must stream via SSE with Time-to-First-Token (TTFT) < 800ms.
5. **Accessibility**: High-contrast UI (>4.5:1 ratio), full keyboard navigation (`Escape`, `Ctrl+Enter`), and ARIA landmarks.
