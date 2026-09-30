<div align="center">

<img src="platform/frontend/public/logo.png" alt="ZeroTrace Logo" width="80" height="80" style="border-radius: 16px; margin-bottom: 8px;" />

# ZeroTrace®

### **Integrated Defense-Grade Data Sanitization & Forensic File Recovery Platform**
*National Forensic & Cybersecurity Platform — NTRO SIH26149*

<p align="center">
  <a href="https://github.com/MK-codes365/zerotrace/stargazers"><img src="https://img.shields.io/github/stars/MK-codes365/zerotrace?color=2563eb&style=for-the-badge&logo=starship&logoColor=white" alt="Stars" /></a>
  <a href="https://github.com/MK-codes365/zerotrace/network/members"><img src="https://img.shields.io/github/forks/MK-codes365/zerotrace?color=4f46e5&style=for-the-badge&logo=git&logoColor=white" alt="Forks" /></a>
  <a href="https://github.com/MK-codes365/zerotrace/issues"><img src="https://img.shields.io/github/issues/MK-codes365/zerotrace?color=0284c7&style=for-the-badge&logo=github&logoColor=white" alt="Issues" /></a>
  <a href="https://github.com/MK-codes365/zerotrace/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-059669?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Vite-7-646CFF?style=flat-square&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/GSAP-3.15-88CE02?style=flat-square&logo=greensock&logoColor=white" />
  <img src="https://img.shields.io/badge/TailwindCSS-v4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/Vercel-Hosted-000000?style=flat-square&logo=vercel&logoColor=white" />
</p>

[🌐 Live Web Platform](#-web-dashboard) • [💻 Desktop Application](#-windows-desktop-tool) • [🛡️ Cryptographic Engine](#-core-algorithms) • [⚡ Quickstart](#-quickstart)

---

</div>

## 🌟 Executive Overview

**ZeroTrace®** unifies irreversible media erasure and forensic-grade data recovery into a single tamper-evident ecosystem. Engineered for defense agencies, law enforcement digital forensic units, and enterprise cybersecurity operations.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ZeroTrace® Ecosystem                            │
├───────────────────────────────────┬────────────────────────────────────┤
│   🛡️ Military-Grade Sanitization  │    🔍 Forensic File Recovery       │
│   • NIST SP 800-88 Clear & Purge  │    • Scalpel Signature Carving     │
│   • DoD 5220.22-M (3/7-Pass)      │    • Bi-Directional Fragment Graph │
│   • Peter Gutmann (35-Pass)       │    • Structural Consensus Scoring  │
├───────────────────────────────────┴────────────────────────────────────┤
│   ⛓️ Cryptographic Ledger: Merkle Tree Roots + SHA-256 Hash Chains     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Algorithmic Architecture

| 🔮 Algorithm / Engine | 🎯 Operational Purpose | 📍 Code Implementation |
| :--- | :--- | :--- |
| **⚙️ Master–Worker** | Parallel sector overwriting & multi-threaded carving | [`windows_tool/engines/nwipe_engine.py`](windows_tool/engines/nwipe_engine.py) |
| **🗺️ MapReduce** | Splits multi-GB disk streams into chunks with overlap windows | [`windows_tool/engines/scalpel_carver.py`](windows_tool/engines/scalpel_carver.py) |
| **🎯 Consensus Scoring** | Evaluates header, footer, chunk syntax & entropy | [`windows_tool/engines/structure_validator.py`](windows_tool/engines/structure_validator.py) |
| **🕸️ Fragment Graph** | Reconstructs non-contiguous clusters across disk gaps | [`windows_tool/engines/scalpel_carver.py`](windows_tool/engines/scalpel_carver.py) |
| **🌲 Merkle Tree** | $O(\log N)$ block integrity proofs for digital certificates | [`windows_tool/core/crypto.py`](windows_tool/core/crypto.py) |
| **⛓️ Hash Chain** | Tamper-evident chronological custody ledger | [`windows_tool/core/audit.py`](windows_tool/core/audit.py) |

---

## 💻 ZeroTrace Desktop Tool

<details open>
<summary><b>🛠️ Desktop Capabilities & Features</b></summary>
<br>

* 🔌 **Low-Level Sector I/O**: Direct Windows raw disk handle access (`\\.\PhysicalDriveX`).
* 🧹 **Certified Sanitizer**: Automated pattern overwriting with zero residual magnetization checks.
* 🔎 **Scalpel Engine**: Deep file carving across raw images (`.E01`, `.DD`, `.RAW`) and damaged drives.
* 📜 **Signed Certificates**: Instant PDF compliance certificates with SHA-256 hashes and QR verification.

```powershell
# Run ZeroTrace Desktop App
cd windows_tool
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```
</details>

---

## 🌐 Web Dashboard & Central Hub

<details open>
<summary><b>📊 Real-Time Web Platform Features</b></summary>
<br>

* 📈 **Live Telemetry Feed**: Real-time I/O throughput (MB/s), sector counters, and active wipe passes.
* 📁 **Desktop Case Sync**: Real-time inspection of cases recorded in `forensic_cases.json`.
* 🛡️ **Client-Side Cryptography**: In-browser Merkle Tree Root computation via Web Crypto API.
* 📜 **Immutable Audit Trail**: Chronological chain validation (`#0 Genesis` to latest block).

```bash
# Run Frontend Locally
cd platform/frontend
npm install
npm run dev
```
</details>

---

## 🚀 Quickstart Guide

```bash
# 1. Clone Repository
git clone https://github.com/MK-codes365/zerotrace.git
cd zerotrace

# 2. Start Web Platform (Vite + React)
cd platform/frontend
npm install
npm run dev

# 3. Launch Desktop Workstation (Admin PowerShell)
cd ../../windows_tool
python main.py
```

---

## 📦 Directory Structure

```
zero-trace/
├── platform/
│   ├── frontend/             # 🌐 React 19 + Vite + GSAP + TailwindCSS v4
│   │   ├── src/components/   # Blue & White Dashboard, Navbar, Footer
│   │   ├── src/sections/     # Hero (60 FPS Video), StickyCols, Welcome
│   │   └── public/           # Live Telemetry, Audit Trail & MSI / EXE Downloads
│   └── backend/              # ⚡ FastAPI + SQLAlchemy + SQLite Engine
├── windows_tool/             # 💻 Python Desktop Application (ZeroTrace.exe)
│   ├── core/                 # Merkle Tree, Hash Chain, Backend Sync, Case Manager
│   ├── engines/              # Scalpel Carver, Nwipe Sanitizer, Structure Validator
│   └── ui/                   # Modern CustomTkinter Forensic Workbench
└── vercel.json               # 🚀 Vercel Production Deployment Configuration
```

---

<div align="center">

### 🛡️ Verified Defense Compliance Standards
`NIST SP 800-88 Rev 1` • `DoD 5220.22-M` • `ISO/IEC 27037` • `Peter Gutmann 35-Pass`

<br>

**Built with pride by [MK-codes365](https://github.com/MK-codes365)**

</div>
