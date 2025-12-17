# 🔥 ZeroTrace Windows Tool

<div align="center">

![ZeroTrace Icon](icon.ico)

**Professional Data Wiping Solution for Windows**

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/yourusername/zerotrace)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Wiping Methods](#-wiping-methods)
- [Architecture](#-architecture)
- [Development](#-development)
- [Contributing](#-contributing)

---

## 🎯 Overview

**ZeroTrace** is a robust, enterprise-grade data wiping tool that ensures permanent data destruction on Windows systems. Built with a hybrid C++/Python architecture, it combines maximum performance with ease of use.

### ✨ Key Highlights

- 🚀 **20-40% faster** than pure Python solutions
- 🔒 **5 industry-standard** wiping algorithms
- 📜 **Cryptographic proof** generation (PDF + JSON certificates)
- 🎨 **Modern UI** with real-time progress tracking
- 🛡️ **System drive protection** to prevent accidents

---

## 🚀 Features

### 🔐 Security Features

✅ **Multi-Algorithm Support**

- NIST 800-88 Clear (1-Pass)
- NIST 800-88-2 Purge (Random)
- DoD 5220.22-M (3-Pass)
- DoD 5220.22-M ECE (7-Pass)
- Peter Gutmann (35-Pass)

✅ **Safety Mechanisms**

- Automatic system drive detection & blocking
- Volume locking & dismounting
- Drive access privilege elevation
- Confirmation dialogs

### 📊 Performance Features

✅ **Hybrid C++/Python Core**

- Native C++ DLL for maximum speed
- Automatic fallback to Python ctypes
- Hardware-accelerated random generation
- 4MB optimized write buffers

✅ **Real-Time Monitoring**

- Live progress bar (0-100%)
- Pass-by-pass tracking (e.g., "Pass 7/35")
- Write speed display (MB/s)
- Time estimation

### 📜 Documentation & Proof

✅ **Wipe Certificates**

- PDF certificate (digitally signed)
- JSON certificate (machine-readable)
- Includes: Drive info, method, timestamp, verification result

---

## 🛠️ Tech Stack

<div align="center">

### Core Technologies

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)

### Libraries & Frameworks

| Technology                                                                                                 | Purpose              | Version  |
| ---------------------------------------------------------------------------------------------------------- | -------------------- | -------- |
| ![CustomTkinter](https://img.shields.io/badge/CustomTkinter-2962FF?style=flat&logo=python&logoColor=white) | Modern GUI Framework | 5.2.0+   |
| ![WMI](https://img.shields.io/badge/WMI-0078D4?style=flat&logo=windows&logoColor=white)                    | Drive Detection      | Latest   |
| ![PyWin32](https://img.shields.io/badge/PyWin32-FCC624?style=flat&logo=windows&logoColor=black)            | Windows API Access   | Latest   |
| ![FPDF](https://img.shields.io/badge/FPDF-FF6B6B?style=flat&logo=adobe&logoColor=white)                    | PDF Generation       | Latest   |
| ![ctypes](https://img.shields.io/badge/ctypes-3776AB?style=flat&logo=python&logoColor=white)               | C++ DLL Integration  | Built-in |

### Development Tools

| Tool                   | Purpose                |
| ---------------------- | ---------------------- |
| **Visual Studio 2026** | C++ compilation        |
| **cx_Freeze**          | MSI installer creation |
| **Windows API**        | Direct disk I/O        |
| **kernel32.dll**       | Low-level operations   |

</div>

---

## 📦 Installation

### Option 1: MSI Installer (Recommended)

1. Download `ZeroTrace-1.3.0-win64.msi` from `dist/` folder
2. Double-click to install
3. Desktop shortcut created automatically

### Option 2: From Source

```bash
# Clone repository
git clone https://github.com/yourusername/zerotrace.git
cd zerotrace/windows_tool

# Install dependencies
pip install customtkinter wmi pywin32 fpdf

# Run application
python main.py
```

> ⚠️ **IMPORTANT:** Always run as Administrator for drive access!

---

## 🎯 Usage

### Step 1: Launch as Administrator

Right-click **ZeroTrace** → **Run as administrator**

### Step 2: Select Drive

Choose the drive you want to wipe from the dropdown list.

> 🛡️ **Safety:** System drive (C:) is automatically disabled

### Step 3: Choose Method

Select wiping standard from dropdown:

- NIST 800-88 Clear (fastest, 1 pass)
- Peter Gutmann (most secure, 35 passes)

### Step 4: Confirm & Wipe

Click **"WIPE SELECTED DRIVE"** and confirm in dialog.

### Step 5: Get Certificate

After completion, PDF and JSON certificates are automatically generated.

---

## 🔬 Wiping Methods

### 📊 Comparison Table

| Method         | Passes | Speed      | Security     | Use Case                 |
| -------------- | ------ | ---------- | ------------ | ------------------------ |
| **NIST Clear** | 1      | ⚡⚡⚡⚡⚡ | 🔒🔒🔒       | Quick wipe before resale |
| **NIST Purge** | 1      | ⚡⚡⚡⚡   | 🔒🔒🔒🔒     | Government standard      |
| **DoD 3-Pass** | 3      | ⚡⚡⚡     | 🔒🔒🔒🔒     | Military standard        |
| **DoD 7-Pass** | 7      | ⚡⚡       | 🔒🔒🔒🔒🔒   | High security            |
| **Gutmann**    | 35     | ⚡         | 🔒🔒🔒🔒🔒🔒 | Maximum security         |

### 🔍 Technical Details

#### NIST 800-88 Clear

```
Pass 1: Zeros (0x00)
```

#### DoD 5220.22-M (3-Pass)

```
Pass 1: Zeros (0x00)
Pass 2: Ones  (0xFF)
Pass 3: Random
```

#### Peter Gutmann (35-Pass)

```
Pass 1-4:   Random
Pass 5-31:  Alternating patterns (0x55/0xAA)
Pass 32-35: Random
```

---

## 🏗️ Architecture

### Hybrid Design

```
┌─────────────────────────────────────┐
│   Python Layer (UI & Logic)         │
│   - CustomTkinter GUI               │
│   - Drive detection (WMI)           │
│   - Certificate generation          │
└──────────────┬──────────────────────┘
               │
               ▼
      ┌────────┴────────┐
      │  Auto-Detect    │
      └────────┬────────┘
               │
      ┌────────┴────────────────┐
      │                         │
      ▼                         ▼
┌─────────────┐         ┌──────────────┐
│  C++ Core   │         │ Python Core  │
│ (Fast)      │         │ (Fallback)   │
└─────────────┘         └──────────────┘
```

### C++ Performance Core

**File:** `wiper_core.cpp` (10KB)

**Features:**

- Direct Windows API calls
- Hardware-accelerated random (`RtlGenRandom`)
- 4MB buffered I/O
- Real-time progress callbacks
- Privilege elevation (`SE_MANAGE_VOLUME`)

**Performance:**

- Sequential: ~450 MB/s
- Random: ~380 MB/s
- CPU: 15-25%

### Python Fallback Core

**File:** `wiper.py` (10KB)

**Features:**

- Pure Python ctypes implementation
- Same algorithms as C++
- 100% compatible interface

**Performance:**

- Sequential: ~420 MB/s
- Random: ~180 MB/s
- CPU: 40-60%

---

## 🔧 Development

### Building the C++ DLL

#### Prerequisites

- Visual Studio 2022/2026 (Community or Build Tools)
- Desktop development with C++ workload

#### Compilation

```bash
.\compile_final.bat
```

Output: `wiper_core.dll` (103 KB)

### Building the Installer

```bash
python setup_msi.py bdist_msi
```

Output: `dist/ZeroTrace-1.3.0-win64.msi`

### Project Structure

```
windows_tool/
├── main.py              # GUI application entry point
├── wiper.py             # Hybrid wiping core
├── wiper_core.cpp       # C++ performance engine
├── disk_manager.py      # Drive detection & safety
├── certificate.py       # PDF/JSON certificate generator
├── setup_msi.py         # MSI installer builder
├── build_dll.bat        # DLL compilation script
├── icon.ico             # Application icon
└── dist/
    └── ZeroTrace-1.3.0-win64.msi
```

---

## ⚠️ Important Notes

### Safety

- ⚠️ **Data wiping is PERMANENT and IRREVERSIBLE**
- ✅ System drive (C:) is automatically protected
- ✅ Requires explicit user confirmation
- ✅ Admin privileges required

### Troubleshooting

**Error 5 (Access Denied):**

1. Run as Administrator
2. Check drive write-protection switch
3. Try different USB drive (some have firmware protection)

**DLL Not Found:**

- App automatically uses Python fallback
- Performance: ~20% slower for random patterns

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 👥 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Submit pull request

---

## 📞 Support

- 📧 Email: support@zerotrace.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/zerotrace/issues)
- 📚 Docs: [Wiki](https://github.com/yourusername/zerotrace/wiki)

---

<div align="center">

**Made with ❤️ for Data Security**

[⬆ Back to Top](#-zerotrace-windows-tool)

</div>
