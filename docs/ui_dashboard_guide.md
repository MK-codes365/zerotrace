# User Interface Dashboard Guide

## 1. Overview
The ZeroTrace UI Dashboard serves as the central command center for all forensic and sanitization operations. It is designed to provide real-time visibility into the hardware and software layers of the system.

## 2. Key Interface Components

### 2.1 Live Telemetry Feed
- **Metrics Displayed**: Real-time read/write speeds (MB/s), current sector being processed, estimated time remaining.
- **Visuals**: Dynamic graphs driven by GSAP animations, updating every few milliseconds.

### 2.2 Case Management Panel
- **Forensic Case Explorer**: Navigate through active and historical investigations.
- **Sync Status**: Displays whether the local desktop client is currently synchronized with the web database.

### 2.3 Audit Logs View
- **Chain Validator**: A dedicated screen to visually inspect the cryptographic hash chain.
- **Block Inspector**: Click on any block to see the Merkle tree root and raw event data associated with that operation.

## 3. Design Aesthetics
The dashboard employs a modern, defense-oriented aesthetic with a sleek color palette. It leverages TailwindCSS v4 to maintain responsive layouts across desktop and mobile, while keeping vital telemetry strictly in focus.
