# ZeroTrace® User Manual

## 1. Getting Started

### 1.1 Prerequisites
- **Operating System**: Windows 10/11 (for Desktop Application).
- **Environment**: Python 3.11+, Node.js (for Web Dashboard).

### 1.2 Installation
**Desktop Workstation:**
1. Open Admin PowerShell.
2. Navigate to `windows_tool`.
3. Create venv: `python -m venv .venv` and activate `.\.venv\Scripts\Activate.ps1`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Run: `python main.py`.

**Web Dashboard:**
1. Navigate to `platform/frontend`.
2. Run `npm install`.
3. Run `npm run dev`.

## 2. Using the Desktop Application
- **Sanitization Mode**: Select the target drive carefully. Choose between DoD 5220.22-M (3/7-Pass), Peter Gutmann (35-Pass), or NIST SP 800-88 Purge.
- **Forensic Recovery Mode**: Point the tool to a raw image or physical drive to begin fragment carving. 
- **Generating Certificates**: Post-operation, click "Generate Certificate" to get a signed, tamper-evident PDF.

## 3. Using the Web Dashboard
- Open `http://localhost:5173` in your browser.
- Monitor active jobs in the real-time telemetry feed.
- Review historical forensic cases and audit logs.
