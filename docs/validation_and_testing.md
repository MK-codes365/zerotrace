# Validation and Testing Documentation

## 1. Unit Testing Strategy
- **Backend Components**: Tested using `pytest`. Modules tested include cryptographic functions, Merkle tree generation, and MapReduce chunks.
- **Frontend Components**: Validated using standard React testing libraries.
- **Hardware Abstraction**: Low-level Windows API calls are mocked during unit tests to prevent accidental data destruction.

## 2. Functional Validation

### 2.1 Data Sanitization
- **Requirement**: Zero residual magnetization.
- **Validation**: Post-wipe verification passes read the entire disk to confirm zero-fill or specified pattern-fill.

### 2.2 Forensic File Recovery
- **Requirement**: High recovery rate from fragmented disks.
- **Validation**: Tested against standard corpus images (e.g., standard NIST CFTT disk images) to confirm signature carving and structural consensus algorithms.

### 2.3 Cryptographic Integrity
- **Requirement**: Tamper-evident ledger.
- **Validation**: Test cases explicitly modify block hashes and ensure the validation engine rejects the modified chain.

## 3. Compliance Testing
ZeroTrace has been evaluated against:
- NIST SP 800-88 Rev 1
- DoD 5220.22-M
- ISO/IEC 27037

All test logs and artifacts are generated and maintained in the `.pytest_cache` and test output directories.
