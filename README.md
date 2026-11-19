# InfraSphere AI — The Intelligent Operating System for Trusted AI

[![Test Suite](https://img.shields.io/badge/pytest-14%2F14%20passing-brightgreen.svg)](docs/EVALUATION_REPORT.md)
[![Security Precision](https://img.shields.io/badge/SecureAI%20Precision-100%25-emerald.svg)](docs/SECURITY_MODEL.md)
[![Audit Verification](https://img.shields.io/badge/SHA--256%20Chain-Cryptographically%20Verified-blueviolet.svg)](docs/SECURITY_MODEL.md)
[![Platform](https://img.shields.io/badge/Platform-InfraOps%20BD%20(Bangladesh)-green.svg)](docs/DATA_PROVENANCE.md)

> **CloudCamp Hackathon 2026** · Flagship Deployment: **InfraOps BD** (Bangladesh Infrastructure Intelligence & Response Platform)

---

## 🌟 Executive Overview

Deploying autonomous AI in high-stakes public infrastructure requires more than simple LLM wrappers. It demands **defense-in-depth against prompt injection, hallucination-free document grounding, explainable task allocation, runaway failure protection, and cryptographic accountability**.

**InfraSphere AI** is a modular-monolith intelligent operations platform integrating **five functioning pillars into one unified real-world workflow**:

1. 🛡️ **SecureAI:** Prompt guard, threat classification, data exfiltration blocker, strict agent tool whitelisting, and execution anomaly detection.
2. 📚 **Knowledge Grid:** Dense Qdrant vector retrieval over operational guidelines with exact page citations (`[DOC-FLD-01 p.1]`), contradiction detection, and 100% evaluated abstention on unanswerable questions.
3. 👥 **WorkforceOS:** Dynamic DAG task decomposition, agent dispatch, and explainable multi-factor candidate scoring:
   $$\text{Score} = 0.40 \cdot \text{Skill} + 0.25 \cdot \text{Zone} + 0.20 \cdot \text{Availability} + 0.15 \cdot \text{Workload}$$
4. ⚡ **AgentOps:** Distributed span tracing, execution telemetry, and automatic circuit breakers (max 10 steps, max 60s, max 3 repeat calls).
5. ⚖️ **Human+AI Governance:** Strict human-in-the-loop sign-off. High-impact operational actions require certified operator authorization before dispatch.
6. 🔒 **Tamper-Evident Ledger:** Every decision and security violation is recorded in an immutable SHA-256 hash chain:
   $$H_i = \text{SHA256}\left(H_{i-1} \parallel \text{CanonicalJSON}(E_i)\right)$$

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+** (Tested on Python 3.13)
- **Node.js 18+** & **npm**

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment (optional)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database and seed demo data (40 incidents, 50 assets, 10 FFWC stations, 6 teams)
python test_init.py

# Run backend API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Documentation will be live at `http://localhost:8000/docs`.*

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Start development command center
npm run dev
```
*Command Center UI will be live at `http://localhost:5173/`.*

---

## 🔑 Default Demo Credentials

The platform includes pre-configured demo personas with 1-click login buttons on the login screen:

| Role | Email | Password | Responsibilities |
|---|---|---|---|
| **Operations Manager** *(Recommended)* | `manager@infrasphere.bd` | `Demo1234!` | Reviews operational recommendations, inspects evidence, approves dispatches. |
| **Infrastructure Analyst** | `analyst@infrasphere.bd` | `Demo1234!` | Analyzes incidents, runs RAG queries, inspects FFWC telemetry. |
| **System Administrator** | `admin@infrasphere.bd` | `Demo1234!` | Manages tool policies, trips/resets circuit breakers, verifies audit ledger. |

---

## 🧪 Testing & Verification

Run the full automated test suite (14 passing tests covering all pillars):
```bash
cd backend
python -m pytest tests/ -v
```

Execute the system evaluation benchmark suite:
```bash
cd backend
python -m app.evaluation.run_all
```
*View comprehensive benchmark results in [`docs/EVALUATION_REPORT.md`](docs/EVALUATION_REPORT.md).*

---

## 📂 Project Directory Structure

```text
infrasphere-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # Triage, Knowledge, Risk, Workforce, Response, Supervisor
│   │   ├── agentops/        # Circuit breaker & trace management
│   │   ├── api/             # FastAPI routers (auth, incidents, secureai, audit, etc.)
│   │   ├── core/            # Config, security, database, and SHA-256 audit chaining
│   │   ├── evaluation/      # Benchmark suites & report generator
│   │   ├── human_ai/        # Approval service & feedback loop
│   │   ├── knowledge/       # Chunking, vector store, embeddings, and RAG
│   │   ├── models/          # SQLAlchemy async data models
│   │   ├── secureai/        # Prompt guard, threat classifier, anomaly detector
│   │   ├── seed/            # 40 incidents, 10 FFWC stations, 6 teams demo data
│   │   └── workforce/       # Task decomposer & team assignment scoring engine
│   └── tests/               # 14 unit and end-to-end integration tests
├── frontend/
│   ├── src/
│   │   ├── components/      # Layout, Sidebar, Header
│   │   ├── context/         # AuthContext with 1-click role switcher
│   │   ├── pages/           # 9 Command Center views (Overview, Incidents, SecureAI, etc.)
│   │   ├── services/        # Axios API client
│   │   └── types/           # TypeScript data interfaces
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── SECURITY_MODEL.md
│   ├── MODEL_CARDS.md
│   ├── DATA_PROVENANCE.md
│   ├── EVALUATION_REPORT.md
│   └── DEMO_SCRIPT.md       # Exact 3-minute hackathon presentation script
├── docker-compose.yml
└── README.md
```

---

## 📜 Ethical Data & Synthetic Telemetry Policy

All incidents, river station measurements, and engineering documents in this demonstration are synthetically modeled for disaster response simulation in Bangladesh. They do not claim to represent live government operations. All data is labeled with `is_synthetic: true` in accordance with [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md).

---

## 🏆 CloudCamp Hackathon 2026 Deliverable
Developed by a solo developer in 48 hours for **CloudCamp Hackathon 2026**.
