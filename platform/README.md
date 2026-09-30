# ZEROTrace

## Integrated Secure Data Erasure & Advanced File Recovery Platform

**SIH26149 — National Technical Research Organisation (NTRO)**

---

### 🛡️ Overview

ZEROTrace is a production-quality prototype for **defensive cybersecurity, digital forensics, and data sanitization**. It combines:

- **Secure Drive Eraser** — Media-aware sanitization with pluggable strategies
- **Secure File & Folder Eraser** — Overwrite-based file deletion with verification
- **Advanced File Carving & Recovery** — Signature-based carving with MapReduce processing
- **Recovery Validation & Classification** — Structure-based validation and auto-classification
- **Evidence Integrity Management** — SHA-256/512, Merkle Trees, tamper-evident Hash Chains
- **Audit Logging** — Hash-chained audit trail for forensic compliance
- **Forensic Reporting** — PDF/JSON/CSV reports and sanitization certificates
- **Dashboard / GUI** — Professional cybersecurity dashboard
- **Job Management** — Master controller with configurable worker pool
- **Verification Engine** — Independent verification of sanitization and recovery

### ⚠️ Safety

```
SAFE_DEMO_MODE=true (default)
```

**No destructive operations occur in demo mode.** Every destructive sanitization operation requires:
1. Authentication
2. Device selection
3. Explicit "CONFIRM SANITIZATION" text
4. Second confirmation checkbox
5. Preflight summary

### 🚀 Quick Start

```bash
# Clone and start
cd platform
docker compose up --build

# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# Swagger:  http://localhost:8000/docs
```

### 🏗️ Architecture

```
Frontend (React + TypeScript + Tailwind + Recharts)
    ↓
API Gateway (FastAPI + Pydantic)
    ↓
Job / Workflow Manager (Master Controller)
    ↓
Processing Engines
    ├── Sanitization Engine
    ├── File Recovery Engine
    ├── File Carving Engine
    ├── Fragment Reconstruction Engine
    ├── Classification Engine
    ├── Validation Engine
    └── Integrity Engine
    ↓
Evidence / Metadata Store (PostgreSQL)
    ↓
Audit + Reporting Engine
```

### 📁 Repository Structure

```
platform/
├── frontend/           # React + TypeScript + Vite
├── backend/            # FastAPI + SQLAlchemy
│   └── app/
│       ├── api/        # REST endpoints
│       ├── core/       # Config, DB, Security, Logging
│       ├── models/     # SQLAlchemy ORM models
│       ├── schemas/    # Pydantic request/response schemas
│       └── services/   # Business logic (demo, etc.)
├── engines/            # Processing engines
│   ├── carving/        # Signature-based file carving
│   ├── classification/ # Automatic file classification
│   ├── integrity/      # SHA-256, Merkle Tree, Hash Chain
│   ├── reconstruction/ # Fragment graph reconstruction
│   ├── recovery/       # Consensus multi-strategy recovery
│   ├── sanitization/   # Pluggable sanitization strategies
│   └── validation/     # Structure-based file validation
├── forensic/           # Audit, Chain of Custody, Reporting
├── workers/            # Master Controller, Worker Pool
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env.example
```

### 🔬 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4, Recharts |
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Auth | JWT + bcrypt + RBAC |
| Container | Docker + Docker Compose |

### 📊 Supported File Types

JPEG, PNG, GIF, BMP, PDF, ZIP, DOCX, XLSX, MP3, WAV, MP4

### 🔐 Sanitization Methods

| Method | Passes | Best For |
|--------|--------|----------|
| ZERO_FILL | 1 | HDD, USB |
| RANDOM_DATA | 1 | HDD, USB |
| DOD_522220M | 3 | HDD |
| GUTMANN | 35 | HDD (legacy) |
| SECURE_ERASE_ATA | 1 | SSD |
| CRYPTO_ERASE | 1 | SED drives |

### 📋 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/register | Register user |
| POST | /api/auth/login | Login |
| POST | /api/cases | Create case |
| GET | /api/cases | List cases |
| POST | /api/evidence | Register evidence |
| POST | /api/evidence/{id}/hash | Hash evidence |
| POST | /api/recovery | Start recovery job |
| POST | /api/sanitization/preview | Preview sanitization |
| POST | /api/sanitization/execute | Execute sanitization |
| POST | /api/integrity/verify | Verify integrity |
| GET | /api/audit | Audit events |
| POST | /api/reports | Generate report |
| GET | /api/dashboard/stats | Dashboard statistics |
| POST | /api/demo/run | Run full demo |
| GET | /api/health | Health check |

### 🎯 SIH Requirement Traceability

See [docs/SIH_REQUIREMENTS.md](docs/SIH_REQUIREMENTS.md)
