# 🔥 ZeroTrace — Unified Forensic & Data Sanitization Workstation

<div align="center">

**Enterprise Digital Forensics & Secure Data Sanitization Platform**  
*Professional Defensive Forensics & Certified Media Destruction*

</div>

---

## 🎯 Architecture & Integrated Repositories

This desktop application combines the algorithmic and forensic capabilities of the top 5 industry-standard digital forensics and data sanitization suites:

| Repository / Engine | Role in ZeroTrace Desktop | Module |
|:---|:---|:---|
| **Nwipe & ShredOS** (`nwipe`, `shredos.x86_64`) | Multi-pass sanitization (NIST 800-88 Clear/Purge, DoD 5220.22-M 3/7-Pass, Gutmann 35-Pass), real-time throughput telemetry (MB/s), ETA countdown, bad sector tracking, post-wipe verification sampling. | **Module 1: Secure Drive Eraser** |
| **Forensic File Shredder** | Selective & batch file/folder shredding, metadata & timestamp zeroing to epoch (1970-01-01), cluster slack space wiping, UUID filename scrambling before unlinking. | **Module 2: File & Folder Eraser** |
| **Scalpel** (`scalpel`) | High-speed signature-based carving engine using `scalpel.conf` rules (covering JPEG, PNG, GIF, BMP, PDF, ZIP/DOCX/XLSX, RAR, 7Z, MP4, MP3, WAV, SQLite, EVTX, Registry hives) with sliding-window extraction. | **Module 3: Advanced File Carving** |
| **The Sleuth Kit** (`sleuthkit`) | Filesystem metadata analysis, NTFS $MFT / FAT deleted record recovery, and Recycle Bin remnant exploration for recovering files with original names and directory paths. | **Module 3: Filesystem Recovery** |
| **TestDisk & PhotoRec** (`testdisk`, `autopsy/thirdparty/photorec_exec`) | Partition table (MBR/GPT) inspection, deep structural validation (JPEG SOF/EOI, PNG IHDR/IEND, PDF xref/trailer, ZIP central directory), confidence scoring (0-100%), and 1-click bridge to bundled 64-bit TestDisk & QPhotoRec tools. | **Structure Validation & Partition Suite** |
| **Autopsy** (`autopsy`) | Case management (Case ID, Investigator, Agency), automatic classification into evidence categories (Images, Documents, Media, Archives, Databases), live Hex & ASCII viewer, and tamper-evident hash-chained audit logging. | **Workbench, Case & Audit Trail** |

---

## 🚀 Workstation Features

### 🛡️ Module 1: Secure Drive Eraser
- **Target Selection**: Detects physical drives and mounted volumes via WMI & Win32 APIs.
- **Media-Aware Classification**: Categorizes drives as HDD (Rotational), SSD (NVMe / Flash), USB (Removable), or SD Card.
- **Safety Protection**: Flags Windows system drive (`C:`, `PhysicalDrive0`) with explicit confirmation gates to prevent accidental system destruction.
- **Real-Time Telemetry**:
  - Live Throughput Speed (MB/s) and moving average speed.
  - Overall Progress % and Current Pass Buffer Progress %.
  - Time remaining (ETA) formatted in `HH:MM:SS`.
  - Bad sector detection and error counters.
  - Independent post-wipe verification sampling.
- **Certification**: Generates tamper-resistant PDF certificates and JSON verification records with HMAC-SHA256 digital signatures.

### 🗂️ Module 2: Secure File & Folder Eraser
- **Selective & Batch Operations**: Multi-select individual files or recursively shred entire directory trees.
- **Residual Trace Cleansing**:
  - Scrambles filenames to random UUIDs before unlinking to eliminate directory entry / MFT remnants.
  - Resets Creation, Last Access, and Last Modified timestamps to Epoch (1970-01-01).
  - Wipes unallocated cluster slack space past EOF.
  - Truncates files to 0 bytes before removal.
- **Standards Supported**: NIST 800-88, DoD 5220.22-M (3-Pass & 7-Pass), Gutmann (35-Pass), Cryptographic Random, Zero Fill.

### 🔍 Module 3: Advanced File Carving & Recovery
- **Multi-Strategy Carving**:
  - **Scalpel Deep Signature Carver**: Scans raw unallocated sectors or forensic disk images (`.dd`, `.raw`, `.img`, `.vhd`, `.iso`) without filesystem metadata.
  - **SleuthKit Filesystem Undelete**: Recovers deleted files using residual MFT and directory records, restoring original names and paths.
  - **Hybrid Consensus Mode**: Merges both engines for maximum file recovery yield.
- **Real-Time Stream**: Live table streaming carved files as they are identified with byte offsets, estimated sizes, and cryptographic SHA-256 digests.

### 🧩 Recovery Workbench & Hex Inspector
- **Autopsy-Style Evidence Classifier**: Group discovered files by category (Images, Documents, Media, Archives, Databases, Filesystem).
- **Confidence Scoring Meter**: Multi-metric scoring (0% to 100%) computed from header match (30%), footer match (25%), structural validation (25%), Shannon entropy (10%), and size plausibility (10%).
- **Raw Hex & ASCII Inspector**: Inspect the first 512 bytes of any carved artifact with offset, hex bytes, and ASCII representation.
- **Evidence Extraction**: Single-file export or batch extraction organizing recovered artifacts into categorized forensic folders.
- **Forensic PDF Case Reports**: Export official court-admissible recovery reports with digital signatures.

### 🛠️ Partition & TestDisk Tools
- Partition table (MBR/GPT) and boot sector diagnostic inspection.
- Direct launch of bundled 64-bit TestDisk (console terminal) and QPhotoRec (Qt GUI).
- Integrated `fidentify` magic-byte signature tester.

### 📜 Tamper-Evident Hash Chain Audit Trail
- Every operation (Drive Wipe, File Shred, Carving, Recovery, Export) is recorded in an immutable append-only hash chain:
  $$\text{Event}[n].\text{hash} = \text{SHA256}(\text{Event}[n-1].\text{hash} + \text{Timestamp} + \text{Action} + \text{Target} + \text{Details})$$
- Cryptographic verification button validates ledger integrity across all blocks.

---

## 💻 Running the Application

Activate the environment and run:

```powershell
cd e:\zero-trace\windows_tool
.\.venv\Scripts\Activate.ps1
python main.py
```
