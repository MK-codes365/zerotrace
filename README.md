# ZeroTrace

<div align="center">

**Secure Data Destruction Tool with NIST-Compliant Wiping**

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://reactjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-Express-339933?logo=node.js)](https://nodejs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Mongoose-47A248?logo=mongodb)](https://mongodb.com/)
[![Python](https://img.shields.io/badge/Python-CustomTkinter-3776AB?logo=python)](https://python.org/)

</div>

---

## What is ZeroTrace?

ZeroTrace is a data wiping tool that permanently erases drives using military and government-grade standards. It ships as a Windows desktop application with a marketing website and a backend server for license management and telemetry.

### Wiping Methods Supported

| Method | Passes | Standard |
|--------|--------|----------|
| NIST 800-88 Clear | 1 | Zero-fill |
| NIST 800-88-2 Purge | 1 | Random data |
| DoD 5220.22-M | 3 | US Department of Defense |
| DoD 5220.22-M ECE | 7 | Extended DoD |
| Peter Gutmann | 35 | Maximum security |

---

## Project Structure

```
zero-trace/
├── website/
│   ├── frontend/          # React + Vite marketing site
│   │   ├── src/
│   │   │   ├── components/    # Hero, Features, Pricing, StatsCounter, etc.
│   │   │   ├── pages/         # Home, About, Cart, Checkout, Privacy, Terms
│   │   │   └── context/       # CartContext for state management
│   │   └── public/
│   └── backend/           # Express + MongoDB API server
│       └── index.js           # Orders, payments, licenses, telemetry
├── windows_tool/          # Python desktop application
│   ├── main.py                # GUI (CustomTkinter)
│   ├── wiper.py               # Wiping engine (C++ DLL + Python fallback)
│   ├── wiper_core.dll         # Native C++ wiping core
│   ├── disk_manager.py        # Drive detection via WMI
│   ├── certificate.py         # PDF certificate generation
│   └── popup_code.py          # Success popup dialog
```

---

## Tech Stack

### Desktop App (Windows)
- **Python 3** with CustomTkinter for the GUI
- **C++ native DLL** for high-performance disk I/O (with Python ctypes fallback)
- **WMI** for drive/volume detection
- **fpdf** for PDF certificate generation

### Website Frontend
- **React 18** with Vite
- **Vanilla CSS** with dark theme and neon accents
- **Razorpay** payment integration (INR)
- **Real-time stats** fetched from backend API

### Backend Server
- **Node.js** with Express
- **MongoDB** with Mongoose ODM
- **Razorpay** signature verification
- **License key** generation and activation tracking
- **Telemetry** aggregation for live dashboard stats

---

## Getting Started

### Prerequisites

- Node.js v16+
- Python 3.10+
- MongoDB (local or Atlas)

### 1. Clone the repo

```bash
git clone https://github.com/MK-codes365/zerotrace.git
cd zerotrace
```

### 2. Website Frontend

```bash
cd website/frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### 3. Backend Server

```bash
cd website/backend
npm install

# Create .env file (copy from example)
cp .env.example .env
# Edit .env with your Razorpay keys and MongoDB URI

npm start
```

Server runs on `http://localhost:5000`

### 4. Desktop App

```bash
cd windows_tool
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install customtkinter wmi pywin32 fpdf
python main.py
```

> **Note:** The desktop app requires Administrator privileges to access raw disk handles for wiping.

---

## Environment Variables

### Backend (`website/backend/.env`)

```env
PORT=5000
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
MONGODB_URI=mongodb://127.0.0.1:27017/zerotrace
```

### Frontend (`website/frontend/.env`)

```env
VITE_RAZORPAY_KEY_ID=your_razorpay_key_id
VITE_API_URL=http://localhost:5000
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/orders` | Create a Razorpay payment order |
| POST | `/api/verify` | Verify payment and generate license keys |
| POST | `/api/activate` | Activate a license key on a device |
| POST | `/api/telemetry` | Log wipe statistics from desktop app |
| GET | `/api/stats` | Get aggregated stats for homepage counters |

---

## How It Works

### Payment Flow
1. User selects a plan on the website and proceeds to checkout.
2. Frontend creates an order via `POST /api/orders`.
3. Razorpay payment modal opens. User pays.
4. On success, `POST /api/verify` validates the payment signature and generates license key(s).
5. Keys are stored in MongoDB and displayed to the user.

### License Activation
1. User opens the desktop app and clicks "Activate License".
2. App sends the key to `POST /api/activate`.
3. Server checks if the key exists, is active, and hasn't exceeded its activation limit.
4. On success, the app unlocks premium wiping methods (DoD, Gutmann, etc.).

### Live Telemetry
1. Desktop app completes a wipe successfully.
2. A background thread sends `{ filesWiped, bytesWiped, method }` to `POST /api/telemetry`.
3. The website homepage polls `GET /api/stats` every 10 seconds.
4. Stats counters (Files Wiped, Data Secured, Active Users) update in real-time.

---

## License Tiers

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| NIST 800-88 Clear | ✅ | ✅ | ✅ |
| DoD 5220.22-M | ❌ | ✅ | ✅ |
| Peter Gutmann (35-Pass) | ❌ | ✅ | ✅ |
| PDF Certificate | ✅ | ✅ | ✅ |
| Max Activations | — | 1 | 5 |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

MIT License

---

<div align="center">

**Built by [MK-codes365](https://github.com/MK-codes365)**

</div>
