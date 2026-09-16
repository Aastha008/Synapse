# 🧠 Synapse — AI Observability & Root Cause Intelligence

> **An event-driven, real-time microservices observability platform with AI-powered Root Cause Analysis (RCA).**

![Architecture Status](https://img.shields.io/badge/System-Active-success)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI_AsyncIO-blue)
![ML Engine](https://img.shields.io/badge/ML-Isolation_Forest_+_Z--Score-orange)
![MongoDB](https://img.shields.io/badge/Raw_Archive-MongoDB-4DB33D)
![LLM](https://img.shields.io/badge/RCA-Gemini_%7C_OpenAI-8A2BE2)
![Frontend](https://img.shields.io/badge/Frontend-React_18_+_TypeScript-cyan)
![WebSockets](https://img.shields.io/badge/RealTime-WebSocket_Stream-brightgreen)

---

## Contents

1. [Problem & Architecture](#-problem--architecture)
2. [Key Engineering Highlights](#-key-engineering-highlights-sde--ml-portfolio)
3. [Tech Stack](#️-tech-stack)
4. [Data Storage: Why Two Databases](#-data-storage-why-two-databases)
5. [API Reference](#-api-reference)
6. [Quick Start](#-quick-start)
7. [Environment Variables](#-environment-variables)
8. [Interactive Scenario Testing](#-interactive-scenario-testing)
9. [Project Structure](#-project-structure)

---

## 📌 Problem & Architecture

In distributed architectures, cascading failures create massive telemetry noise: when a downstream database slows down, multiple upstream services start timing out, spiking errors and latencies across the fleet.

This platform simulates real-time microservices traffic, continuously ingests logs and metrics via an asynchronous event bus, detects statistical & machine learning anomalies, and executes an **AI Root Cause Analysis (RCA)** engine using service dependency graphs to pinpoint the exact root cause in seconds.

```
                  Applications (Microservices Fleet)
                                 ↓
                     Telemetry / Logs / Events
                                 ↓
                   Asynchronous Event Bus / Queue
                                 ↓
                       Log Processing Engine
                    ┌────────────┼────────────┐
                    ↓            ↓            ↓
            Anomaly Detection  Metrics    Raw Event Archive
           (Isolation Forest    Engine        (MongoDB,
             + Z-Score)      (Sliding Window   schema-less
                              Aggregator)       payloads)
                    ↓            ↓                 │
                    └─────┬──────┘                 │
                          ↓                         │
              AI Root Cause Analysis (RCA)  ←───────┘
       (Dependency Graph Walk + Gemini / OpenAI Reasoner,
              grounded in raw log evidence)
                          ↓
                Real-Time Web Dashboard
             (WebSocket Streaming + Recharts)
```

The raw archive sits off the hot path deliberately — every event still gets archived, but the anomaly detector never waits on it. It's only read back once, at incident time, to give the RCA engine (and the LLM prompt) real log evidence instead of just aggregate numbers.

---

## 🌟 Key Engineering Highlights (SDE & ML Portfolio)

### 1. Distributed Systems & Concurrency (SDE)
- **Async Event Pipeline**: Non-blocking asynchronous publisher-subscriber queue architecture (`asyncio.Queue`) handling high-throughput log/metric streams with backpressure control and fan-out distribution.
- **Microservices Topology**: Models realistic multi-tier service dependencies (`API Gateway` → `Payment Service` / `User Service` / `Notification Service` → `Database`).

### 2. Machine Learning & Statistical Anomaly Detection (AI/ML)
- **Dual-Tier Detection Engine**:
  - **Statistical Fast Path**: Real-time sliding window rolling mean and standard deviation Z-score detector (`|z| > 2.5`).
  - **Multivariate ML Path**: Rolling `Isolation Forest` trained continuously on multi-dimensional metric vectors to discover subtle multivariate correlations and outlier states.

### 3. AI Root Cause Analysis (RCA)
- **Graph-Based Dependency Traversal**: Pinpoints the true failure origin by traversing directed dependency graphs and scoring anomalous dependents.
- **Gemini AI Root Cause Reasoning**: Powered by Google Gemini (`GEMINI_API_KEY`), converting structured graph findings and raw log excerpts directly into plain-English incident narratives, impact summaries, and actionable SRE remediation checklists.
- **Automated Incident Reports**: Delivers severity ratings, confidence scores, chronological anomaly evidence timelines, and dependency chains backed by real log lines.

### 4. Polyglot Persistence
- **SQLite** (`aiosqlite`) for structured, aggregatable telemetry — logs, metrics, and incident records.
- **MongoDB** (`motor`) used as the active raw event archive — high-throughput, non-blocking ingestion of raw JSON payloads, queried for real log evidence during incident investigations. See [Data Storage](#-data-storage-why-two-databases) below.

### 5. Data Analytics & Time-Series Engine
- **In-Memory Ring Buffer Aggregation**: Real-time percentile computation (P50, P95, P99), error distribution analytics, and velocity/trend direction indicators.

### 6. Full-Stack Real-Time Dashboard
- **React 18 + TypeScript + Vite + Tailwind CSS + Recharts**:
  - Real-time **System Health Cards** with dynamic threshold coloring
  - **Active Incident Command Center** with AI confidence gauge and remediation steps
  - **Live Service Topology Map** with health status animations
  - **2×2 Telemetry Time-Series Grid**
  - **Live Monospace Log Stream** with pause/resume functionality
  - **Error Distribution Pie Chart**

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, AsyncIO, Uvicorn |
| Structured storage | SQLite (`aiosqlite`), Pydantic v2 |
| Raw event archive | MongoDB (`motor`) — Used for raw telemetry storage & log evidence |
| ML / Analytics | Scikit-Learn (Isolation Forest), NumPy, SciPy |
| AI reasoning | Google Gemini API (Gemini API Key configured for RCA reasoning), OpenAI API (fallback) via `httpx` |
| Real-time | WebSockets (`WSMessage` protocol) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4, Recharts, Lucide Icons |

---

## 🗄️ Data Storage: Why Two Databases

Structured telemetry — durations, error counts, percentiles — fits a relational schema cleanly, so it stays in **SQLite**. Raw log payloads don't share a fixed shape: a database error carries connection-pool internals, a payment error carries a different set of fields entirely. Forcing that into rigid SQL columns means either dropping fields or filling tables with unused nullable columns.

So every raw event is also archived, untouched, into a **MongoDB** `raw_events` collection — deliberately *off* the hot detection path (fire-and-forget, never blocking the anomaly detector) and read back only once: when `root_cause_analyzer.py` needs real evidence for a confirmed incident, or when the AI reasoner needs to quote an actual log line instead of paraphrasing a confidence score. Documents expire automatically after `RAW_EVENT_TTL_SECONDS` (7 days by default) via a Mongo TTL index, so the archive doesn't grow unbounded.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Current system health snapshot |
| GET | `/api/health/services/{service}` | Health for a single service |
| GET | `/api/health/history` | Historical health data |
| GET | `/api/incidents` | List recent incidents |
| GET | `/api/incidents/active` | Currently active incidents |
| GET | `/api/incidents/{incident_id}` | Full incident detail |
| GET | `/api/incidents/{incident_id}/raw-logs` | Raw MongoDB log evidence for an incident |
| GET | `/api/metrics/timeseries` | Time-series for one metric |
| GET | `/api/metrics/all-timeseries` | Time-series for all tracked metrics |
| GET | `/api/metrics/summary` | Aggregated metric summary |
| GET | `/api/metrics/errors` | Error distribution breakdown |
| GET | `/api/logs` | Recent structured logs |
| GET | `/api/scenario/trigger?name=...` | Trigger a failure scenario |
| GET | `/api/scenario/reset` | Reset all services to baseline |
| WS | `/ws` | Live dashboard stream (health, logs, incidents) |

---

## 🚦 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- **MongoDB** instance (used for raw log archiving via `MONGO_URI`) — e.g. [Atlas free tier](https://www.mongodb.com/cloud/atlas/register) or local instance
- **Gemini API Key** (used for AI-driven RCA narratives) — obtain from [Google AI Studio](https://aistudio.google.com/)

### 1. Backend Setup & Run
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # configure your GEMINI_API_KEY and MONGO_URI in .env
python run.py
```
The FastAPI backend starts at `http://127.0.0.1:8000` with a WebSocket endpoint at `ws://127.0.0.1:8000/ws`. With MongoDB and the Gemini API key configured, Synapse automatically archives raw events and generates AI-powered root-cause incident analyses.

### 2. Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser to view the real-time observability dashboard.

---

## 🔑 Environment Variables

Configure these settings in `backend/.env` (both **MongoDB** and **Gemini API Key** are integrated):

| Variable | Status / Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | **Configured** | Google Gemini API key used for generating AI Root Cause Analysis (RCA) narratives |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model used for RCA reasoning |
| `MONGO_URI` | **Configured** | MongoDB connection URI used for the raw event archive |
| `MONGO_DB_NAME` | `synapse` | MongoDB database name |
| `RAW_EVENT_TTL_SECONDS` | `604800` (7 days) | Auto-expiry for archived raw events in MongoDB |
| `OPENAI_API_KEY` | Optional (fallback) | Fallback LLM provider if Gemini isn't set |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model used if fallback path is active |

---

## 🔬 Interactive Scenario Testing

The dashboard features **one-click scenario simulation**:

1. Click **"Trigger Incident"** in the top navigation bar (or call `GET /api/scenario/trigger?name=db_connection_exhaustion`).
2. Watch the telemetry stream:
   - Database connection pool starts climbing from 40% to 94%+.
   - Payment Service query latency jumps 4.2×.
   - API Gateway error rates spike.
3. The **Anomaly Detector** flags deviations and passes them to the **Root Cause Analyzer**, which pulls matching raw log evidence from MongoDB (if configured).
4. An incident is detected:
   - **Severity**: `HIGH` / `CRITICAL`
   - **Root Cause**: *Database connection pool exhaustion in database-service causing cascading failures.*
   - **Confidence**: `87%`
   - **Affected Services**: `database-service`, `payment-service`, `api-gateway`
5. Click **"Reset"** to return all services to baseline operating health.

---

## 📂 Project Structure

```
Synapse/
├── backend/
│   ├── analytics/
│   │   ├── anomaly_detector.py      # Dual-tier Z-Score + Isolation Forest ML
│   │   ├── metrics_engine.py        # Sliding-window metrics & percentiles
│   │   └── root_cause_analyzer.py   # Graph walk + Gemini/OpenAI reasoning + raw evidence
│   ├── api/
│   │   ├── routes/                  # REST routers (health, incidents, metrics, logs)
│   │   ├── websocket.py             # WebSocket broadcasting manager
│   │   └── main.py                  # FastAPI lifespan & application setup
│   ├── database/
│   │   ├── db.py                    # Async SQLite connection & schema DDL
│   │   ├── repository.py            # Structured data access layer
│   │   ├── mongo.py                 # MongoDB connection manager (raw archive)
│   │   └── mongo_repository.py      # Raw event write/query functions
│   ├── models/
│   │   └── schemas.py               # Pydantic data contracts
│   ├── pipeline/
│   │   ├── queue.py                 # Async pub/sub event queue
│   │   └── processor.py             # Telemetry worker & orchestrator
│   ├── simulator/
│   │   ├── log_generator.py         # Realistic distributed traffic generator
│   │   └── scenario_engine.py       # Pre-built failure injection scenarios
│   ├── config.py                    # Service baselines, thresholds & env config
│   ├── .env.example                 # All optional environment variables
│   ├── requirements.txt
│   └── run.py                       # Server entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx           # Controls & socket connection indicator
│   │   │   ├── SystemHealthPanel.tsx# Metric health cards
│   │   │   ├── IncidentPanel.tsx    # RCA command center
│   │   │   ├── ServiceMap.tsx       # Live topology graph
│   │   │   ├── MetricsCharts.tsx    # 2×2 telemetry charts
│   │   │   ├── LogViewer.tsx        # Real-time streaming log terminal
│   │   │   └── ErrorDistribution.tsx# Error distribution breakdown
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts      # Resilient WebSocket hook
│   │   ├── services/
│   │   │   └── api.ts               # API client
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```
