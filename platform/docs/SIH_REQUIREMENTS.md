# SIH26149 — Requirement Traceability Matrix

## Design and Development of an Integrated Secure Data Erasure and Advanced File Recovery Tool for Digital Forensics and Data Sanitization

**Organization: National Technical Research Organisation (NTRO)**

---

| # | SIH Requirement | Module | Path | Status |
|---|----------------|--------|------|--------|
| 1 | Secure Drive Eraser | Sanitization Engine | `engines/sanitization/` | ✅ Implemented |
| 2 | Secure File & Folder Eraser | File Eraser (in Sanitization) | `engines/sanitization/` (FileEraser class) | ✅ Implemented |
| 3 | Advanced File Carving | Carving Engine | `engines/carving/` | ✅ Implemented |
| 4 | Fragment Reconstruction | Reconstruction Engine | `engines/reconstruction/` | ✅ Implemented |
| 5 | Automatic Classification | Classification Engine | `engines/classification/` | ✅ Implemented |
| 6 | Confidence Scoring | Consensus Recovery + Validation | `engines/recovery/` + `engines/validation/` | ✅ Implemented |
| 7 | Audit Logging | Forensic Audit Service | `forensic/` (AuditService) | ✅ Implemented |
| 8 | Forensic Reporting | Report Generator | `forensic/` (ReportGenerator) | ✅ Implemented |
| 9 | Multiple Storage Devices | Device Detection | `engines/sanitization/` (DeviceInfo, MediaType) | ✅ Implemented |
| 10 | Multiple Filesystems | Filesystem Adapters | `engines/sanitization/` + evidence model | ✅ Architecture |
| 11 | Tamper-resistant Reporting | Integrity Engine | `engines/integrity/` (MerkleTree, HashChain) | ✅ Implemented |
| 12 | User Interface Dashboard | React Frontend | `frontend/src/pages/` | ✅ Implemented |
| 13 | Performance Evaluation | Worker Pool Metrics | `workers/master_controller/` | ✅ Implemented |
| 14 | Evidence Management | Evidence Registry | `backend/app/models/` + `backend/app/api/` | ✅ Implemented |
| 15 | Chain of Custody | Custody Service | `forensic/` (ChainOfCustodyService) | ✅ Implemented |
| 16 | Hash Verification | Integrity Engine | `engines/integrity/` (SHA-256, SHA-512) | ✅ Implemented |
| 17 | Job Management | Master Controller | `workers/master_controller/` | ✅ Implemented |
| 18 | MapReduce Processing | Chunk Generator + Workers | `workers/master_controller/` | ✅ Implemented |
| 19 | Safe Demo Mode | Config + Sanitization Engine | `backend/app/core/config.py` | ✅ Implemented |
| 20 | Authentication & RBAC | Security Module | `backend/app/core/security.py` | ✅ Implemented |
| 21 | REST API | FastAPI Endpoints | `backend/app/api/endpoints.py` | ✅ Implemented |
| 22 | Database Design | SQLAlchemy Models (17 tables) | `backend/app/models/` | ✅ Implemented |
| 23 | Sanitization Certificate | Report Generator | `forensic/` (generate_sanitization_certificate) | ✅ Implemented |
| 24 | Docker Deployment | Docker Compose | `docker-compose.yml` | ✅ Implemented |
| 25 | Synthetic Test Data | Demo Service | `backend/app/services/demo_service.py` | ✅ Implemented |

---

### Forensic Recovery Pipeline

```
Evidence Image → Read-only Mount → SHA-256 → Master Controller → Chunk Generator
→ Worker Pool → MAP → Signature Detection → Candidate Extraction
→ Structure Validation → Fragment Detection → Graph Reconstruction
→ Consensus Scoring → Classification → Validation → SHA-256
→ Merkle Tree → Hash Chain → Forensic Report
```

### Sanitization Pipeline

```
Target Device → Device Detection → Capability Detection → Sanitization Strategy
→ Preflight → Explicit Confirmation → Sanitization → Independent Verification
→ Hash/Evidence Record → Audit Log → Tamper-Evident Report → Certificate
```
