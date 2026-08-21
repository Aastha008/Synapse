# 🧠 Synapse — AI Observability & Root Cause Intelligence

> **An event-driven, real-time microservices observability platform with AI-powered Root Cause Analysis (RCA).**

![Architecture Status](https://img.shields.io/badge/System-Active-success)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI_AsyncIO-blue)
![ML Engine](https://img.shields.io/badge/ML-Isolation_Forest_+_Z--Score-orange)
![Frontend](https://img.shields.io/badge/Frontend-React_18_+_TypeScript-cyan)
![WebSockets](https://img.shields.io/badge/RealTime-WebSocket_Stream-brightgreen)

---

## 📌 Problem & High-Level Architecture

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
                             ↓
             ┌───────────────┴───────────────┐
             ↓                               ↓
     Anomaly Detection                Metrics Engine
(Isolation Forest + Z-Score)     (Sliding Window Aggregator)
             ↓                               ↓
             └───────────────┬───────────────┘
                             ↓
                 AI Root Cause Analysis (RCA)
             (Dependency Graph Walk + AI Reasoner)
                             ↓
                 Real-Time Web Dashboard
              (WebSocket Streaming + Recharts)
```

---

## 🌟 Key Engineering Highlights (SDE & ML Portfolio)

### 1. **Distributed Systems & Concurrency (SDE)**
- **Async Event Pipeline**: Uses non-blocking asynchronous publisher-subscriber queue architecture (`asyncio.Queue`) handling high-throughput log/metric streams with backpressure control and fan-out distribution.
- **Microservices Topology**: Models realistic multi-tier service dependencies (`API Gateway` → `Payment Service` / `User Service` / `Notification Service` → `Database`).

### 2. **Machine Learning & Statistical Anomaly Detection (AI/ML)**
- **Dual-Tier Detection Engine**:
  - **Statistical Fast Path**: Real-time sliding window rolling mean and standard deviation Z-score detector ($|z| > 2.5$).
  - **Multivariate ML Path**: Rolling `Isolation Forest` trained continuously on multi-dimensional metric vectors to discover subtle multivariate correlations and outlier states.

### 3. **AI Root Cause Analysis (RCA)**
- **Graph-Based Dependency Traversal**: Pinpoints the true failure origin by traversing directed acyclic graphs (DAGs) and scoring anomalous dependents.
- **Automated Incident Reasoning**: Generates structured incident reports including:
  - Incident severity level & confidence score
  - Plain-English root cause explanation
  - Chronological evidence timeline
  - Actionable SRE remediation checklist

### 4. **Data Analytics & Time-Series Engine**
- **In-Memory Ring Buffer Aggregation**: Real-time percentile computation ($P_{50}$, $P_{95}$, $P_{99}$), error distribution analytics, and velocity/trend direction indicators.

### 5. **Full-Stack Real-Time Dashboard**
- **React 18 + TypeScript + Vite + Tailwind CSS + Recharts**:
  - Real-time **System Health Cards** with dynamic threshold coloring
  - **Active Incident Command Center** with AI confidence gauge and remediation steps
  - **Live Service Topology Map** with health status animations
  - **2x2 Telemetry Time-Series Grid**
  - **Live Monospace Log Stream** with pause/resume functionality
  - **Error Distribution Pie Chart**

---

## 🛠️ Tech Stack

- **Backend**: Python 3.14, FastAPI, AsyncIO, Uvicorn, SQLite (`aiosqlite`), Pydantic v2
- **ML / Analytics**: Scikit-Learn (Isolation Forest), NumPy, SciPy
- **Real-Time Communication**: WebSockets (`WSMessage` protocol)
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS v4, Recharts, Lucide Icons

---

## 🚦 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup & Run
```bash
cd backend
pip install -r requirements.txt
python run.py
```
*The FastAPI backend will start at `http://127.0.0.1:8000` with WebSocket endpoint at `ws://127.0.0.1:8000/ws`.*

### 2. Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
*Open `http://localhost:5173` in your browser to view the real-time observability dashboard.*

---

## 🔬 Interactive Scenario Testing

The dashboard features **one-click scenario simulation**:

1. Click **"Trigger Incident"** in the top navigation bar (or call `GET /api/scenario/trigger?name=db_connection_exhaustion`).
2. Watch the telemetry stream:
   - Database connection pool starts climbing from 40% to 94%+.
   - Payment Service query latency jumps 4.2×.
   - API Gateway error rates spike.
3. The **Anomaly Detector** flags deviations and passes them to the **Root Cause Analyzer**.
4. An incident is detected:
   - **Severity**: `HIGH` / `CRITICAL`
   - **Root Cause**: *Database connection pool exhaustion in database-service causing cascading failures.*
   - **Confidence**: `87%`
   - **Affected Services**: `database-service`, `payment-service`, `api-gateway`
5. Click **"Reset"** to return all services to baseline operating health.

---

## 📂 Project Structure

```
incident-intelligence/
├── backend/
│   ├── analytics/
│   │   ├── anomaly_detector.py      # Dual-tier Z-Score + Isolation Forest ML
│   │   ├── metrics_engine.py        # Sliding-window metrics & percentiles
│   │   └── root_cause_analyzer.py   # AI RCA & dependency graph walk
│   ├── api/
│   │   ├── routes/                  # Modular REST routers (health, incidents, metrics, logs)
│   │   ├── websocket.py             # WebSocket broadcasting manager
│   │   └── main.py                  # FastAPI lifespan & application setup
│   ├── database/
│   │   ├── db.py                    # Async SQLite connection & schema DDL
│   │   └── repository.py            # Data access layer
│   ├── models/
│   │   └── schemas.py               # Pydantic data contracts
│   ├── pipeline/
│   │   ├── queue.py                 # Async pub/sub event queue
│   │   └── processor.py             # Telemetry worker & orchestrator
│   ├── simulator/
│   │   ├── log_generator.py         # Realistic distributed traffic generator
│   │   └── scenario_engine.py       # Pre-built failure injection scenarios
│   ├── config.py                    # Service baselines & thresholds
│   ├── requirements.txt
│   └── run.py                       # Server entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx           # Controls & socket connection indicator
│   │   │   ├── SystemHealthPanel.tsx# Metric health cards
│   │   │   ├── IncidentPanel.tsx    # RCA Command center
│   │   │   ├── ServiceMap.tsx       # Live topology graph
│   │   │   ├── MetricsCharts.tsx    # 2x2 Telemetry charts
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
