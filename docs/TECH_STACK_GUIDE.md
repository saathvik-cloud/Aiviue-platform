# 🛠️ TECH STACK & FRAMEWORK GUIDE
## Production-Grade Agentic System

**Version:** 1.0  
**Date:** 2026-01-22  
**Purpose:** Framework selection and event-driven architecture guide

---

## 📋 TABLE OF CONTENTS

1. [Final Tech Stack](#1-final-tech-stack)
2. [Framework Decision](#2-framework-decision)
3. [Event-Driven Architecture](#3-event-driven-architecture)
4. [Evolution Path](#4-evolution-path)
5. [Project Structure](#5-project-structure)
6. [Dependencies](#6-dependencies)

---

## 1. FINAL TECH STACK

### 1.1 Complete Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION TECH STACK                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   LAYER              │  TECHNOLOGY           │  PURPOSE                                │
│   ─────────────────  │  ────────────────────  │  ────────────────────────────────────  │
│                                                                                         │
│   API                │  FastAPI              │  REST APIs, webhooks, async support     │
│   Orchestration      │  LangGraph            │  Agent workflows, state, checkpoints    │
│   LLM Components     │  LangChain            │  Tools, prompts, parsers, LLM wrappers  │
│   LLM Provider       │  Groq (Llama 3.3)     │  Fast inference                         │
│   Event Bus          │  Redis Streams        │  Event-driven messaging                 │
│   Task Queue         │  Redis Streams        │  Background task processing             │
│   Cache              │  Redis                │  Sessions, caching, rate limits         │
│   Checkpoints        │  Redis (MVP)          │  Workflow state persistence             │
│   Database           │  PostgreSQL           │  Source of truth                        │
│   Vector Store       │  chromaDB (MVP)          │  Semantic search                        │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Why Each Technology

| Technology | Why Chosen | Alternatives Rejected |
|------------|------------|----------------------|
| **FastAPI** | Async, fast, type hints, OpenAPI | Flask (no async), Django (heavy) |
| **LangGraph** | Built-in checkpointing, explicit control | CrewAI (too magical) |
| **LangChain** | Component library, wide LLM support | Direct API calls (reinventing) |
| **Redis Streams** | Simple, same Redis for everything | Kafka (overkill for MVP) |
| **PostgreSQL** | Reliable, JSON support, industry standard | MongoDB (less relational) |
| **chromadb** | Local, free, good for MVP | Pinecone (cost for MVP) |

---

## 2. FRAMEWORK DECISION

### 2.1 Framework Comparison

| Aspect | LangChain | LangGraph | CrewAI |
|--------|-----------|-----------|--------|
| **Core Purpose** | Components | Orchestration | Role-based agents |
| **Orchestration** | Manual | ✅ Built-in | ✅ Built-in |
| **Checkpointing** | Manual | ✅ Built-in | Limited |
| **Control Level** | High | ✅ High | Low (hidden) |
| **Debugging** | Hard | ✅ Clear traces | Hard |
| **Production Ready** | Needs work | ✅ Yes | Needs hardening |

### 2.2 Decision: LangGraph + LangChain Components

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           FRAMEWORK ARCHITECTURE                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────────┐     │
│   │                    LANGGRAPH (Orchestration Layer)                           │     │
│   │                                                                              │     │
│   │   • Workflow definition (graphs)                                             │     │
│   │   • State management (TypedDict)                                             │     │
│   │   • Checkpointing (Redis/PostgreSQL)                                         │     │
│   │   • Conditional routing                                                      │     │
│   │   • Human-in-the-loop                                                        │     │
│   └──────────────────────────────────────────────────────────────────────────────┘     │
│                                    │                                                    │
│                    ┌───────────────┼───────────────┐                                    │
│                    │               │               │                                    │
│                    ▼               ▼               ▼                                    │
│               ┌─────────┐    ┌─────────┐    ┌─────────┐                                │
│               │ Agent 1 │    │ Agent 2 │    │ Agent 3 │                                │
│               │  Node   │    │  Node   │    │  Node   │                                │
│               └────┬────┘    └────┬────┘    └────┬────┘                                │
│                    │              │              │                                      │
│   ┌────────────────┴──────────────┴──────────────┴────────────────────────────────┐    │
│   │                    LANGCHAIN (Component Layer)                                │    │
│   │                                                                               │    │
│   │   • ChatGroq (LLM wrapper)         • BaseTool (tool definitions)              │    │
│   │   • PromptTemplate                 • OutputParser (JSON, Pydantic)            │    │
│   │   • Document loaders               • Text splitters                           │    │
│   │   • chromadb integration              • Embeddings                               │    │
│   └───────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 What NOT to Use

| Technology | Reason |
|------------|--------|
| **CrewAI** | Too magical, hides control, hard to debug |
| **AutoGen** | Complex, Microsoft-specific patterns |
| **Custom Orchestration** | Reinventing the wheel |
| **Celery (for MVP)** | Overkill, add later if needed |
| **Kafka (for MVP)** | Overkill, add when scaling to millions |

---

## 3. EVENT-DRIVEN ARCHITECTURE

### 3.1 Why Event-Driven?

```
SYNCHRONOUS (Bad for agents):
User Request → Agent 1 → Agent 2 → Agent 3 → Response
              │         │          │
              └─ BLOCKING, user waits 30+ seconds

EVENT-DRIVEN (Production pattern):
User Request → Publish Event → Return "Processing" (immediate)
                    │
                    ▼
              Background Worker → Agent 1 → Agent 2 → Agent 3
                                  │         │          │
                                  └─ Non-blocking, async updates
```

### 3.2 Redis Streams as Event Bus

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         REDIS STREAMS ARCHITECTURE                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   PRODUCERS (API/Webhooks)                                                              │
│   ├── Webhook received → XADD events:candidate * type "LEAD_RECEIVED" data "{...}"     │
│   ├── User action → XADD events:candidate * type "MESSAGE_RECEIVED" data "{...}"       │
│   └── Scheduler → XADD events:scheduled * type "DAILY_SUMMARY" data "{...}"            │
│                                                                                         │
│   ─────────────────────────────────────────────────────────────────────────────────     │
│                                                                                         │
│   REDIS STREAMS                                                                         │
│   ├── events:candidate     (candidate-related events)                                   │
│   ├── events:job           (job-related events)                                         │
│   ├── events:employer      (employer-related events)                                    │
│   └── events:scheduled     (scheduled/cron events)                                      │
│                                                                                         │
│   ─────────────────────────────────────────────────────────────────────────────────     │
│                                                                                         │
│   CONSUMERS (Worker Processes)                                                          │
│   ├── XREADGROUP GROUP workers worker-1 STREAMS events:candidate >                      │
│   ├── Route to handler based on event type                                              │
│   ├── Execute LangGraph workflow                                                        │
│   ├── Checkpoint to Redis                                                               │
│   └── XACK on completion                                                                │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Event Types for Your System

| Event | Stream | Triggers |
|-------|--------|----------|
| `LEAD_RECEIVED` | events:candidate | Lead webhook |
| `RESUME_UPLOADED` | events:candidate | WhatsApp/Web upload |
| `MESSAGE_RECEIVED` | events:candidate | WhatsApp webhook |
| `JOB_CREATED` | events:job | Employer action |
| `SCREENING_COMPLETED` | events:candidate | Agent completion |
| `VOICE_OUTCOME` | events:candidate | Voice API webhook |
| `EMPLOYER_ACTION` | events:employer | Dashboard action |
| `DAILY_SUMMARY` | events:scheduled | Scheduler |

### 3.4 Why Redis Streams over Celery (MVP)

| Aspect | Redis Streams | Celery |
|--------|---------------|--------|
| **Setup** | ✅ Already have Redis | Need broker + backend |
| **Ordering** | ✅ Guaranteed | ❌ Not guaranteed |
| **Replay** | ✅ Built-in | ❌ No |
| **Learning** | ✅ Simple API | Steeper curve |
| **Dependencies** | None extra | celery + flower + backend |

**Add Celery later when:** Need scheduled tasks, complex routing, or built-in monitoring

---

## 4. EVOLUTION PATH

### 4.1 Scaling Stages

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              EVOLUTION PATH                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   STAGE 1: MVP (0 - 10K users) ← YOU ARE HERE                                          │
│   ═════════════════════════════                                                         │
│   Events:      Redis Streams                                                            │
│   Tasks:       Redis Streams + asyncio workers                                          │
│   Workflow:    LangGraph + Redis checkpointing                                          │
│   Vector:      FAISS (local)                                                            │
│                                                                                         │
│   ─────────────────────────────────────────────────────────────────────────────────     │
│                                                                                         │
│   STAGE 2: Growth (10K - 100K users)                                                    │
│   ══════════════════════════════════                                                    │
│   Events:      Redis Streams (scaled)                                                   │
│   Tasks:       Redis Streams + worker pool                                              │
│   Workflow:    LangGraph + PostgreSQL checkpointing                                     │
│   Vector:      FAISS + caching                                                          │
│   NEW:         Redis Cluster, Read replicas                                             │
│                                                                                         │
│   ─────────────────────────────────────────────────────────────────────────────────     │
│                                                                                         │
│   STAGE 3: Scale (100K - 1M users)                                                      │
│   ═════════════════════════════════                                                     │
│   Events:      Kafka (for high-throughput)                                              │
│   Tasks:       Celery + Redis broker                                                    │
│   Workflow:    LangGraph + Kafka events                                                 │
│   Vector:      Pinecone (managed)                                                       │
│                                                                                         │
│   ─────────────────────────────────────────────────────────────────────────────────     │
│                                                                                         │
│   STAGE 4: Massive (1M+ users)                                                          │
│   ═════════════════════════════                                                         │
│   Events:      Kafka (full)                                                             │
│   Tasks:       Celery + Kafka                                                           │
│   Workflow:    Temporal (or LangGraph at scale)                                         │
│   Vector:      Managed (Pinecone/Weaviate)                                              │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 When to Add What

| Need | Add | When |
|------|-----|------|
| Scheduled tasks | Celery | When cron jobs get complex |
| Task monitoring | Flower | With Celery |
| Millions of events | Kafka | >100K events/sec |
| Managed vectors | Pinecone | Scale or team grows |
| Complex workflows | Temporal | Extreme durability needs |

---

## 5. PROJECT STRUCTURE

```
your_agentic_app/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── candidates.py
│   │   │   ├── jobs.py
│   │   │   └── webhooks.py       # External webhooks
│   │   ├── dependencies.py
│   │   └── middleware.py
│   │
│   ├── events/
│   │   ├── __init__.py
│   │   ├── schemas.py            # Event Pydantic models
│   │   ├── publisher.py          # XADD to Redis Streams
│   │   ├── consumer.py           # XREADGROUP from Streams
│   │   └── handlers/
│   │       ├── __init__.py
│   │       ├── candidate.py      # LEAD_RECEIVED, MESSAGE_RECEIVED
│   │       ├── job.py            # JOB_CREATED
│   │       └── employer.py       # EMPLOYER_ACTION
│   │
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── screening.py          # LangGraph workflow
│   │   ├── matching.py
│   │   └── engagement.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py              # TypedDict for LangGraph
│   │   ├── base.py               # Base agent class
│   │   ├── job_intelligence.py
│   │   ├── candidate_ingestion.py
│   │   ├── qualification.py
│   │   ├── engagement.py
│   │   ├── voice.py
│   │   ├── employer_value.py
│   │   └── ops_governance.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── document.py           # Resume parsing
│   │   ├── search.py             # Candidate search
│   │   └── messaging.py          # WhatsApp tools
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── redis_client.py       # Redis connection
│   │   ├── session.py            # Session management
│   │   └── checkpointer.py       # LangGraph checkpointer
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database/             # SQLAlchemy models
│   │   │   ├── candidate.py
│   │   │   ├── job.py
│   │   │   └── ...
│   │   └── schemas/              # Pydantic schemas
│   │       ├── requests.py
│   │       └── responses.py
│   │
│   ├── config/ 
│   │   ├── __init__.py
│   │   ├── settings.py           # Pydantic Settings
│   │   └── prompts/
│   │       ├── job_intelligence.py
│   │       └── ...
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   └── event_worker.py       # Background event processor
│   │
│   └── main.py                   # FastAPI app
│
├── scripts/
│   ├── start_api.py
│   ├── start_workers.py
│   └── healthcheck.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── workflows/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 6. DEPENDENCIES

### 6.1 MVP Requirements

```python
# requirements.txt

# ═══════════════════════════════════════════════════════
# CORE FRAMEWORK
# ═══════════════════════════════════════════════════════

# API
fastapi>=0.110.0
uvicorn>=0.27.0
python-multipart>=0.0.9

# ═══════════════════════════════════════════════════════
# AGENT FRAMEWORK
# ═══════════════════════════════════════════════════════

# LangGraph (includes LangChain core)
langgraph>=0.2.0
langchain>=0.3.0
langchain-core>=0.3.0

# LLM Provider
langchain-groq>=0.2.0

# Checkpointing
langgraph-checkpoint>=2.0.0

# ═══════════════════════════════════════════════════════
# DATA STORES
# ═══════════════════════════════════════════════════════

# Redis (events + cache + sessions)
redis>=5.0.0

# PostgreSQL
asyncpg>=0.29.0
sqlalchemy>=2.0.0
alembic>=1.13.0

# Vector Store (MVP)
faiss-cpu>=1.7.0

# ═══════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════

# Data Validation
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Environment
python-dotenv>=1.0.0

# Logging
structlog>=24.0.0

# HTTP Client
httpx>=0.27.0

# Document Processing
pypdf>=4.0.0
python-docx>=1.0.0
```

### 6.2 Later Additions

```python
# Add when scaling (Stage 2/3)
# ═══════════════════════════════════════════════════════

# Task Queue (when need scheduling)
celery>=5.4.0
flower>=2.0.0

# Kafka (when millions of events)
confluent-kafka>=2.3.0

# Managed Vector (when scaling)
pinecone-client>=3.0.0

# PostgreSQL Checkpointing (production)
langgraph-checkpoint-postgres>=2.0.0
```

---

## 📋 QUICK REFERENCE

### Stack Summary

| Layer | MVP | Scale |
|-------|-----|-------|
| **API** | FastAPI | FastAPI (load balanced) |
| **Orchestration** | LangGraph | LangGraph |
| **Events** | Redis Streams | Kafka |
| **Tasks** | Redis Streams | Celery |
| **Cache** | Redis | Redis Cluster |
| **Database** | PostgreSQL | PostgreSQL (replicated) |
| **Vector** | FAISS | Pinecone |

### Decision Summary

| Question | Answer |
|----------|--------|
| LangGraph or CrewAI? | **LangGraph** |
| Celery or Redis Streams? | **Redis Streams** (MVP) |
| Kafka now? | **No** (add at scale) |
| What from LangChain? | Components only (LLMs, tools, prompts) |

---
