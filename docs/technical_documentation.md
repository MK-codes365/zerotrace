# ZeroTrace® Technical Documentation

## 1. System Architecture
ZeroTrace® is designed as a hybrid platform featuring a Python-based Desktop Application (Windows) for low-level sector operations and a web-based React/FastAPI Dashboard for telemetry and auditing.

### 1.1 Desktop Application (ZeroTrace Desktop Tool)
- **Language**: Python 3.11
- **Key Modules**:
  - `nwipe_engine.py`: Handles parallel sector overwriting.
  - `scalpel_carver.py`: Performs deep file carving on raw images and physical drives.
  - `structure_validator.py`: Evaluates header, footer, and block consistency.
  - `crypto.py` & `audit.py`: Maintains cryptographic Merkle Trees and hash chains for compliance.

### 1.2 Web Dashboard
- **Frontend**: React 19, Vite 7, TailwindCSS v4, GSAP.
- **Backend**: FastAPI, SQLAlchemy, SQLite.
- **Features**: Live telemetry feed, client-side cryptographic verification, real-time audit ledger.

## 2. Cryptographic Core
- **Merkle Tree Proofs**: Guarantees block integrity for digital certificates ($O(\log N)$).
- **Hash Chains**: Provides a tamper-evident chronological custody ledger.

## 3. Deployment
- **Desktop**: Standalone executable compiled via PyInstaller or run natively through Python virtual environment.
- **Web**: Hosted on Vercel (Frontend) and standard ASGI servers like Uvicorn for FastAPI (Backend).
