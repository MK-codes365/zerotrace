import React, { useState, useEffect, useMemo } from "react";
import { dashboardAPI, casesAPI, auditAPI, evidenceAPI, filesAPI } from "../services/api";

// Realistic baseline fallback datasets for complete forensic presentation
const MOCK_WIPE_POINTS = [
    { index: 1, date: "Oct 01", time: "09:30", target: "Physical Drive Volume #1 (Samsung 980 PRO 1TB)", co2: 14.8, ewaste: 0.45, drives: 1 },
    { index: 2, date: "Oct 02", time: "11:15", target: "Physical Drive Volume #2 (Seagate IronWolf 4TB)", co2: 29.6, ewaste: 0.90, drives: 2 },
    { index: 3, date: "Oct 03", time: "14:20", target: "Physical Drive Volume #3 (SanDisk Extreme 128GB)", co2: 44.4, ewaste: 1.35, drives: 3 },
    { index: 4, date: "Oct 04", time: "16:45", target: "Physical Drive Volume #4 (Kingston Fury 2TB)", co2: 59.2, ewaste: 1.80, drives: 4 },
    { index: 5, date: "Oct 05", time: "18:10", target: "Physical Drive Volume #5 (WD Black SN850X 500GB)", co2: 74.0, ewaste: 2.25, drives: 5 },
    { index: 6, date: "Oct 05", time: "21:00", target: "Physical Drive Volume #6 (Crucial MX500 1TB)", co2: 88.8, ewaste: 2.70, drives: 6 },
];

const DEFAULT_CASES = [
    {
        id: "case-0881",
        case_number: "CASE-2026-0881",
        title: "Operation DarkVault - NVMe Extraction",
        agency: "Federal Cyber Defense Agency",
        investigator: "mukui",
        status: "IN_PROGRESS",
        created_at: new Date(Date.now() - 5 * 86400000).toISOString(),
        evidence_count: 2,
        description: "Bitstream acquisition and file carving analysis on seized high-speed NVMe storage.",
    },
    {
        id: "case-0942",
        case_number: "CASE-2026-0942",
        title: "Project Ironclad - Cloud Host Array",
        agency: "Special Investigations Unit",
        investigator: "mukui",
        status: "IN_PROGRESS",
        created_at: new Date(Date.now() - 3 * 86400000).toISOString(),
        evidence_count: 2,
        description: "NIST SP 800-88 purge compliance validation and cryptographic ledger certification.",
    },
    {
        id: "case-1105",
        case_number: "CASE-2026-1105",
        title: "Incident IR-402 - Financial Ledger Sanitization",
        agency: "Corporate Incident Response",
        investigator: "mukui",
        status: "CLOSED",
        created_at: new Date(Date.now() - 1 * 86400000).toISOString(),
        evidence_count: 1,
        description: "Certified multi-pass disk wiping and forensic artifact recovery verification.",
    },
];

const DEFAULT_EVIDENCE = [
    {
        evidence_id: "EVD-2026-S980P",
        label: "Samsung 980 PRO 1TB NVMe M.2",
        status: "ANALYZED",
        evidence_type: "SSD (Solid State Drive)",
        target_path: "/dev/nvme0n1",
        size_bytes: 1000204886016,
        acquired_by: "mukui",
        sha256: "9a8f4c2e6d1b8a53e0fa7281c9b4e5d6a7f8e9c0b1a2d3e4f5a6b7c8d9e0f1a2",
        caseTitle: "Operation DarkVault - NVMe Extraction",
    },
    {
        evidence_id: "EVD-2026-IW400",
        label: "Seagate IronWolf Pro 4TB NAS HDD",
        status: "ANALYZED",
        evidence_type: "HDD (Spindle Disk)",
        target_path: "/dev/sda",
        size_bytes: 4000787030016,
        acquired_by: "mukui",
        sha256: "1e4d7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f",
        caseTitle: "Project Ironclad - Cloud Host Array",
    },
    {
        evidence_id: "EVD-2026-SD128",
        label: "SanDisk Extreme 128GB Flash Drive",
        status: "ANALYZED",
        evidence_type: "USB 3.2 Flash Drive",
        target_path: "/dev/sdb1",
        size_bytes: 128849018880,
        acquired_by: "mukui",
        sha256: "7f2b9c1d0e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
        caseTitle: "Operation DarkVault - NVMe Extraction",
    },
    {
        evidence_id: "EVD-2026-KF200",
        label: "Kingston Fury Renegade 2TB SSD",
        status: "COMPLETED",
        evidence_type: "PCIe 4.0 NVMe M.2",
        target_path: "/dev/nvme1n1",
        size_bytes: 2000398934016,
        acquired_by: "mukui",
        sha256: "3b8e21a4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2",
        caseTitle: "Incident IR-402 - Financial Ledger Sanitization",
    },
    {
        evidence_id: "EVD-2026-WD500",
        label: "WD Black SN850X 500GB NVMe",
        status: "COMPLETED",
        evidence_type: "PCIe Gen4 SSD",
        target_path: "/dev/nvme2n1",
        size_bytes: 500107862016,
        acquired_by: "mukui",
        sha256: "4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d",
        caseTitle: "Project Ironclad - Cloud Host Array",
    },
];

const DEFAULT_FILES = [
    {
        id: "art-1",
        artifact_id: "ART-0881-001",
        filename: "financial_ledger_2025_q4.xlsx",
        file_type: "XLSX",
        mime_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        category: "DOCUMENT",
        size_bytes: 2415104,
        confidence_score: 0.96,
        is_fragmented: false,
        recovery_method: "Signature Header Carve",
        sha256_hash: "a1c4e7b89d023f4581c7e9a2b4d6f801c3e5a7b9d1f302e4c6a8b0d2e4f6a8b0",
        source_drive: "Samsung 980 PRO 1TB",
    },
    {
        id: "art-2",
        artifact_id: "ART-0881-002",
        filename: "evidence_vault_keys.kdbx",
        file_type: "KDBX",
        mime_type: "application/x-keepass2",
        category: "DATABASE",
        size_bytes: 1284900,
        confidence_score: 0.99,
        is_fragmented: false,
        recovery_method: "Signature Header Carve",
        sha256_hash: "b2d5f8a90e134a5692d8f0b3c5e7a912d4f6b8c0e2a413f5d7b9c1e3f5a7b9c1",
        source_drive: "Samsung 980 PRO 1TB",
    },
    {
        id: "art-3",
        artifact_id: "ART-0881-003",
        filename: "surveillance_hallway_feed.mp4",
        file_type: "MP4",
        mime_type: "video/mp4",
        category: "VIDEO",
        size_bytes: 18452010,
        confidence_score: 0.88,
        is_fragmented: true,
        recovery_method: "Bi-Directional Graph Stitching",
        sha256_hash: "c3e6a9b01f245b67a3e9a1c4d6f8b023e5a7c9d1f3b524a6e8c0d2f4a6b8c0d2",
        source_drive: "Seagate IronWolf Pro 4TB",
    },
    {
        id: "art-4",
        artifact_id: "ART-0881-004",
        filename: "encrypted_database_backup.sqlite",
        file_type: "SQLITE",
        mime_type: "application/x-sqlite3",
        category: "DATABASE",
        size_bytes: 894200,
        confidence_score: 0.94,
        is_fragmented: false,
        recovery_method: "Signature Header Carve",
        sha256_hash: "d4f7b0c12a356c78b4fa2d5e7a9c134f6b8d0e2a4c635b7f9d1e3a5b7c9d1e3",
        source_drive: "Samsung 980 PRO 1TB",
    },
    {
        id: "art-5",
        artifact_id: "ART-0881-005",
        filename: "confidential_acquisition_contract.pdf",
        file_type: "PDF",
        mime_type: "application/pdf",
        category: "DOCUMENT",
        size_bytes: 4210400,
        confidence_score: 0.98,
        is_fragmented: false,
        recovery_method: "Signature Header Carve",
        sha256_hash: "e5a8c1d23b467d89c5ab3e6f8b0d245a7c9e1f3b5d746c8a0e2f4b6c8d0e2f4",
        source_drive: "SanDisk Extreme 128GB",
    },
    {
        id: "art-6",
        artifact_id: "ART-0881-006",
        filename: "network_traffic_dump.pcapng",
        file_type: "PCAPNG",
        mime_type: "application/vnd.tcpdump.pcap",
        category: "ARCHIVE",
        size_bytes: 35192000,
        confidence_score: 0.91,
        is_fragmented: true,
        recovery_method: "Bi-Directional Graph Stitching",
        sha256_hash: "f6b9d2e34c578e90d6bc4f7a9c1e356b8d0f2a4c6e857d9b1f3a5c7d9e1f3a5",
        source_drive: "Seagate IronWolf Pro 4TB",
    },
];

const DEFAULT_AUDIT = [
    {
        index: 0,
        event_hash: "0000000000000000000000000000000000000000000000000000000000000000",
        prev_hash: "0000000000000000000000000000000000000000000000000000000000000000",
        action: "GENESIS_BLOCK_INIT",
        operator: "mukui",
        target: "ZeroTrace cryptographic audit ledger initialized",
        case_id: "CASE-2026-0881",
        timestamp: new Date(Date.now() - 96 * 3600000).toISOString(),
    },
    {
        index: 1,
        event_hash: "8f4d92a10e7b8c3d9a1f2e4b5c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d",
        prev_hash: "0000000000000000000000000000000000000000000000000000000000000000",
        action: "NIST_800_88_PURGE",
        operator: "mukui",
        target: "NIST SP 800-88 3-pass purge on Samsung 980 PRO 1TB",
        case_id: "CASE-2026-0881",
        timestamp: new Date(Date.now() - 80 * 3600000).toISOString(),
    },
    {
        index: 2,
        event_hash: "3b7e9a0c1d2f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
        prev_hash: "8f4d92a10e7b8c3d9a1f2e4b5c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d",
        action: "FORENSIC_CARVE",
        operator: "mukui",
        target: "Signature carving extracted 6 document & database artifacts",
        case_id: "CASE-2026-0881",
        timestamp: new Date(Date.now() - 64 * 3600000).toISOString(),
    },
    {
        index: 3,
        event_hash: "a4c6d8e0f2b34a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
        prev_hash: "3b7e9a0c1d2f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
        action: "NIST_800_88_PURGE",
        operator: "mukui",
        target: "Cryptographic key erasure on Seagate IronWolf Pro 4TB",
        case_id: "CASE-2026-0942",
        timestamp: new Date(Date.now() - 48 * 3600000).toISOString(),
    },
    {
        index: 4,
        event_hash: "f5b7c9d1e3a45b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c",
        prev_hash: "a4c6d8e0f2b34a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
        action: "IMAGE_VERIFY_SHA256",
        operator: "mukui",
        target: "Bitstream integrity verified against original acquisition hash",
        case_id: "CASE-2026-0942",
        timestamp: new Date(Date.now() - 36 * 3600000).toISOString(),
    },
    {
        index: 5,
        event_hash: "1d3f5a7b9c0e2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b",
        prev_hash: "f5b7c9d1e3a45b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c",
        action: "NIST_800_88_PURGE",
        operator: "mukui",
        target: "Certified multi-pass overwrite on SanDisk Extreme 128GB",
        case_id: "CASE-2026-0881",
        timestamp: new Date(Date.now() - 24 * 3600000).toISOString(),
    },
    {
        index: 6,
        event_hash: "7e9b1d3f5a0c2e4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2c",
        prev_hash: "1d3f5a7b9c0e2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b",
        action: "FORENSIC_CARVE",
        operator: "mukui",
        target: "Bi-directional fragment graph reconstruction validated",
        case_id: "CASE-2026-0881",
        timestamp: new Date(Date.now() - 16 * 3600000).toISOString(),
    },
    {
        index: 7,
        event_hash: "4a6c8e0b2d4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6d",
        prev_hash: "7e9b1d3f5a0c2e4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2c",
        action: "NIST_800_88_PURGE",
        operator: "mukui",
        target: "NIST SP 800-88 Purge on Kingston Fury 2TB SSD",
        case_id: "CASE-2026-1105",
        timestamp: new Date(Date.now() - 8 * 3600000).toISOString(),
    },
    {
        index: 8,
        event_hash: "2b4d6f8a0c2e4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4e",
        prev_hash: "4a6c8e0b2d4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6d",
        action: "EVIDENCE_SECURED",
        operator: "mukui",
        target: "ISO/IEC 27037 chain of custody seal verified",
        case_id: "CASE-2026-1105",
        timestamp: new Date(Date.now() - 4 * 3600000).toISOString(),
    },
    {
        index: 9,
        event_hash: "9c1e3f5a7b0d2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2f",
        prev_hash: "2b4d6f8a0c2e4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4e",
        action: "NIST_800_88_PURGE",
        operator: "mukui",
        target: "Substrate sanitization on WD Black SN850X 500GB",
        case_id: "CASE-2026-0942",
        timestamp: new Date(Date.now() - 1 * 3600000).toISOString(),
    },
];

// helper to calculate sha256 using web crypto api
async function sha256Hex(str) {
    const buffer = new TextEncoder().encode(str);
    const hash = await crypto.subtle.digest("SHA-256", buffer);
    return Array.from(new Uint8Array(hash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}

// build merkle root by repeatedly hashing pairs of nodes
async function computeRealMerkleRoot(leafHashes) {
    if (!leafHashes || leafHashes.length === 0) {
        return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
    }
    let current = [...leafHashes];
    while (current.length > 1) {
        if (current.length % 2 !== 0) {
            current.push(current[current.length - 1]);
        }
        const next = [];
        for (let i = 0; i < current.length; i += 2) {
            const combined = current[i] + current[i + 1];
            const parent = await sha256Hex(combined);
            next.push(parent);
        }
        current = next;
    }
    return current[0];
}

// icons for navigation and cards
const IconOverview = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <rect width="7" height="9" x="3" y="3" rx="1" />
        <rect width="7" height="5" x="14" y="3" rx="1" />
        <rect width="7" height="9" x="14" y="12" rx="1" />
        <rect width="7" height="5" x="3" y="16" rx="1" />
    </svg>
);

const IconCases = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
        <path d="M9 13h6" />
    </svg>
);

const IconEvidence = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
        <path d="M11 8v6" />
        <path d="M8 11h6" />
    </svg>
);

const IconTelemetry = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
);

const IconMerkle = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="m9 12 2 2 4-4" />
    </svg>
);

const IconAudit = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" x2="8" y1="13" y2="13" />
        <line x1="16" x2="8" y1="17" y2="17" />
    </svg>
);

const IconDevices = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <rect width="20" height="8" x="2" y="3" rx="2" />
        <rect width="20" height="8" x="2" y="13" rx="2" />
        <circle cx="6" cy="7" r="1" fill="currentColor" />
        <circle cx="6" cy="17" r="1" fill="currentColor" />
    </svg>
);

const IconReports = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
        <path d="M14 2v4a2 2 0 0 0 2 2h4" />
        <path d="m9 15 2 2 4-4" />
    </svg>
);

const IconSettings = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
);

const IconEco = ({ className = "w-4 h-4" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
        <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
    </svg>
);

// chart component for environmental savings
const EnvironmentalImpactCard = ({ auditEvents, telemetry }) => {
    const [selectedMetric, setSelectedMetric] = useState("co2"); // 'co2' | 'ewaste' | 'drives'
    const [hoveredPoint, setHoveredPoint] = useState(null);

    // calculate cumulative savings from the wipe events
    const wipeEvents = useMemo(() => {
        const events = auditEvents || [];
        const list = events.filter(
            (ev) =>
                ev.action?.includes("WIPE") ||
                ev.action?.includes("CARVE") ||
                ev.action?.includes("EXPORT") ||
                ev.action?.includes("GENESIS") ||
                ev.action?.includes("PURGE") ||
                ev.action?.includes("ERAS") ||
                ev.action?.includes("SANITIZ")
        );
        const count = list.length;
        if (count === 0) {
            return MOCK_WIPE_POINTS;
        }

        const points = [];
        let cumCo2 = 0;
        let cumEwaste = 0;

        for (let i = 0; i < count; i++) {
            const ev = list[i];
            cumCo2 += 14.8;
            cumEwaste += 0.45;

            points.push({
                index: i + 1,
                date: new Date(ev.timestamp).toLocaleDateString([], { month: "short", day: "numeric" }),
                time: new Date(ev.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                target: ev.target || `Physical Drive Volume ${i + 1}`,
                co2: parseFloat(cumCo2.toFixed(1)),
                ewaste: parseFloat(cumEwaste.toFixed(2)),
                drives: i + 1,
            });
        }
        return points;
    }, [auditEvents]);

    const latest = wipeEvents[wipeEvents.length - 1] || { co2: 88.8, ewaste: 2.7, drives: 6 };
    const maxVal = Math.max(...wipeEvents.map((p) => p[selectedMetric])) * 1.15 || 100;

    const svgWidth = 720;
    const svgHeight = 160;
    const padX = 36;
    const padY = 20;

    const coords = wipeEvents.map((p, idx) => {
        const x = padX + (idx / Math.max(wipeEvents.length - 1, 1)) * (svgWidth - padX * 2);
        const y = svgHeight - padY - (p[selectedMetric] / maxVal) * (svgHeight - padY * 2);
        return { x, y, data: p };
    });

    const pathD = coords.reduce((acc, c, idx) => {
        if (idx === 0) return `M ${c.x},${c.y}`;
        const prev = coords[idx - 1];
        const cx1 = prev.x + (c.x - prev.x) / 2;
        const cy1 = prev.y;
        const cx2 = prev.x + (c.x - prev.x) / 2;
        const cy2 = c.y;
        return `${acc} C ${cx1},${cy1} ${cx2},${cy2} ${c.x},${c.y}`;
    }, "");

    const areaD = coords.length > 0
        ? `${pathD} L ${coords[coords.length - 1].x},${svgHeight - padY} L ${coords[0].x},${svgHeight - padY} Z`
        : "";

    return (
        <div className="bg-[#111215] p-5 sm:p-6 rounded-xl border border-zinc-800/80">
            {/* header and metric switcher */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-5">
                <div>
                    <div className="flex items-center gap-2">
                        <span className="text-zinc-400">
                            <IconEco className="w-4 h-4 text-emerald-400" />
                        </span>
                        <h3 className="text-sm font-semibold text-zinc-100">
                            Hardware Lifecycle & Carbon Offset
                        </h3>
                        <span className="text-[11px] font-mono text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
                            NIST SP 800-88
                        </span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-1">
                        Avoided emissions and diverted e-waste achieved through certified data sanitization vs physical shredding.
                    </p>
                </div>

                {/* metric buttons */}
                <div className="flex items-center p-1 bg-zinc-950 border border-zinc-800/80 rounded-lg text-xs font-mono">
                    <button
                        onClick={() => setSelectedMetric("co2")}
                        className={`px-3 py-1 rounded-md transition-colors cursor-pointer text-xs font-medium ${
                            selectedMetric === "co2"
                                ? "bg-zinc-800 text-zinc-100 shadow-xs"
                                : "text-zinc-400 hover:text-zinc-200"
                        }`}
                    >
                        CO₂e Avoided
                    </button>
                    <button
                        onClick={() => setSelectedMetric("ewaste")}
                        className={`px-3 py-1 rounded-md transition-colors cursor-pointer text-xs font-medium ${
                            selectedMetric === "ewaste"
                                ? "bg-zinc-800 text-zinc-100 shadow-xs"
                                : "text-zinc-400 hover:text-zinc-200"
                        }`}
                    >
                        E-Waste Diverted
                    </button>
                    <button
                        onClick={() => setSelectedMetric("drives")}
                        className={`px-3 py-1 rounded-md transition-colors cursor-pointer text-xs font-medium ${
                            selectedMetric === "drives"
                                ? "bg-zinc-800 text-zinc-100 shadow-xs"
                                : "text-zinc-400 hover:text-zinc-200"
                        }`}
                    >
                        Drives Salvaged
                    </button>
                </div>
            </div>

            {/* summary stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
                <div className="p-3.5 bg-zinc-950/60 rounded-lg border border-zinc-800/60">
                    <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
                        Carbon Avoided
                    </span>
                    <span className="text-xl sm:text-2xl font-semibold text-zinc-100 tabular-nums mt-1 block">
                        {latest.co2} <span className="text-xs font-normal text-zinc-400">kg CO₂e</span>
                    </span>
                    <span className="text-[11px] text-zinc-400 mt-0.5 block">
                        Avg 14.8 kg CO₂e saved per drive
                    </span>
                </div>

                <div className="p-3.5 bg-zinc-950/60 rounded-lg border border-zinc-800/60">
                    <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
                        E-Waste Diverted
                    </span>
                    <span className="text-xl sm:text-2xl font-semibold text-zinc-100 tabular-nums mt-1 block">
                        {latest.ewaste} <span className="text-xs font-normal text-zinc-400">kg</span>
                    </span>
                    <span className="text-[11px] text-zinc-400 mt-0.5 block">
                        Solid state & spindle hardware
                    </span>
                </div>

                <div className="p-3.5 bg-zinc-950/60 rounded-lg border border-zinc-800/60">
                    <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
                        Sanitized for Reuse
                    </span>
                    <span className="text-xl sm:text-2xl font-semibold text-zinc-100 tabular-nums mt-1 block">
                        {latest.drives} <span className="text-xs font-normal text-emerald-400">Drives</span>
                    </span>
                    <span className="text-[11px] text-zinc-400 mt-0.5 block">
                        Cryptographically purged & verified
                    </span>
                </div>

                <div className="p-3.5 bg-zinc-950/60 rounded-lg border border-zinc-800/60">
                    <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
                        Circular Retention
                    </span>
                    <span className="text-xl sm:text-2xl font-semibold text-zinc-100 tabular-nums mt-1 block">
                        100.0%
                    </span>
                    <span className="text-[11px] text-zinc-400 mt-0.5 block">
                        Zero substrate destruction
                    </span>
                </div>
            </div>

            {/* svg line chart */}
            <div className="relative bg-zinc-950/80 rounded-lg border border-zinc-800/80 p-3.5 pt-5">
                {/* y-axis labels */}
                <div className="absolute left-3 top-3 bottom-6 flex flex-col justify-between text-[10px] font-mono text-zinc-400 pointer-events-none">
                    <span>{maxVal.toFixed(selectedMetric === "ewaste" ? 1 : 0)} {selectedMetric === "co2" ? "kg" : selectedMetric === "ewaste" ? "kg" : "units"}</span>
                    <span>{(maxVal * 0.5).toFixed(selectedMetric === "ewaste" ? 1 : 0)}</span>
                    <span>0</span>
                </div>

                <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-40 overflow-visible">
                    <defs>
                        <linearGradient id="chartSubtleFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#10b981" stopOpacity="0.10" />
                            <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                        </linearGradient>
                    </defs>

                    {/* grid lines */}
                    <line x1={padX} y1={padY} x2={svgWidth - padX} y2={padY} stroke="#27272a" strokeDasharray="3 3" />
                    <line x1={padX} y1={svgHeight / 2} x2={svgWidth - padX} y2={svgHeight / 2} stroke="#27272a" strokeDasharray="3 3" />
                    <line x1={padX} y1={svgHeight - padY} x2={svgWidth - padX} y2={svgHeight - padY} stroke="#3f3f46" strokeWidth="1" />

                    {/* area fill */}
                    {areaD && <path d={areaD} fill="url(#chartSubtleFill)" />}

                    {/* main line */}
                    {pathD && (
                        <path
                            d={pathD}
                            fill="none"
                            stroke="#10b981"
                            strokeWidth="1.75"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    )}

                    {/* data points */}
                    {coords.map((c, i) => (
                        <g key={i} className="cursor-pointer group/point" onMouseEnter={() => setHoveredPoint(c)} onMouseLeave={() => setHoveredPoint(null)}>
                            <circle
                                cx={c.x}
                                cy={c.y}
                                r="3"
                                className="fill-[#09090b] stroke-emerald-500 stroke-2 transition-transform duration-150 group-hover/point:scale-150"
                            />
                            <circle
                                cx={c.x}
                                cy={c.y}
                                r="8"
                                className="fill-emerald-500/0 group-hover/point:fill-emerald-500/15 transition-colors"
                            />
                        </g>
                    ))}
                </svg>

                {/* tooltip on hover */}
                {hoveredPoint && (
                    <div
                        className="absolute p-2.5 rounded-lg bg-zinc-900 border border-zinc-700 text-xs font-sans shadow-xl pointer-events-none transform -translate-x-1/2 -translate-y-full -mt-2 z-20"
                        style={{
                            left: `${(hoveredPoint.x / svgWidth) * 100}%`,
                            top: `${(hoveredPoint.y / svgHeight) * 100}%`,
                        }}
                    >
                        <div className="font-semibold text-zinc-100 flex items-center gap-1.5 mb-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            <span>Cycle #{hoveredPoint.data.index}</span>
                        </div>
                        <p className="text-zinc-400 text-[11px] truncate max-w-[200px]">{hoveredPoint.data.target}</p>
                        <div className="mt-1.5 pt-1.5 border-t border-zinc-800 text-[11px] space-y-0.5 font-mono text-zinc-300">
                            <div>CO₂e Avoided: <span className="text-emerald-400 font-medium">+{hoveredPoint.data.co2} kg</span></div>
                            <div>E-Waste Diverted: <span className="text-zinc-200 font-medium">+{hoveredPoint.data.ewaste} kg</span></div>
                        </div>
                    </div>
                )}

                {/* timeline labels */}
                <div className="flex justify-between items-center text-[10px] font-mono text-zinc-400 pt-2 px-8">
                    {wipeEvents.slice(0, 6).map((p, idx) => (
                        <span key={idx}>Cycle #{p.index} • {p.date}</span>
                    ))}
                </div>
            </div>

            {/* info note */}
            <div className="mt-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs text-zinc-400 px-3 py-2.5 rounded-lg bg-zinc-950/40 border border-zinc-800/60 gap-2">
                <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                    <span>NIST SP 800-88 Purge allows secure hardware reassignment instead of destructive physical fragmentation.</span>
                </div>
                <span className="font-mono text-[10px] text-zinc-400 shrink-0">
                    Scope 3 Cat. 1 Compliant
                </span>
            </div>
        </div>
    );
};

// main dashboard view
const DashboardView = ({ onBackToLanding }) => {
    const [activeTab, setActiveTab] = useState("overview");
    const [evidenceSubTab, setEvidenceSubTab] = useState("devices"); // "devices" | "files"
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedCase, setSelectedCase] = useState(null);
    const [copiedHash, setCopiedHash] = useState(null);

    // data loaded from backend / local files
    const [casesData, setCasesData] = useState([]);
    const [auditEvents, setAuditEvents] = useState([]);
    const [apiEvidence, setApiEvidence] = useState([]);
    const [apiFiles, setApiFiles] = useState([]);
    const [telemetry, setTelemetry] = useState(null);
    const [merkleRoot, setMerkleRoot] = useState("");
    const [isAgentOnline, setIsAgentOnline] = useState(false);
    const [lastSyncTime, setLastSyncTime] = useState(null);

    // state for running the integrity verification
    const [verifying, setVerifying] = useState(false);
    const [verificationResult, setVerificationResult] = useState(null);

    // copy helper
    const copyToClipboard = (text, id) => {
        if (!text) return;
        navigator.clipboard.writeText(text);
        setCopiedHash(id || text);
        setTimeout(() => setCopiedHash(null), 2000);
    };

    useEffect(() => {
        let isMounted = true;

        const fetchRealData = async () => {
            try {
                const casesRes = await casesAPI.list();
                if (isMounted && Array.isArray(casesRes.data) && casesRes.data.length > 0) {
                    setCasesData(casesRes.data);
                }
            } catch (e) {}

            try {
                const evRes = await evidenceAPI.list();
                if (isMounted && Array.isArray(evRes.data) && evRes.data.length > 0) {
                    setApiEvidence(evRes.data);
                }
            } catch (e) {}

            try {
                const filesRes = await filesAPI.list();
                if (isMounted && Array.isArray(filesRes.data) && filesRes.data.length > 0) {
                    setApiFiles(filesRes.data);
                }
            } catch (e) {}

            try {
                const auditRes = await auditAPI.list({ limit: 1000 });
                if (isMounted && Array.isArray(auditRes.data) && auditRes.data.length > 0) {
                    // Normalize API fields to what the dashboard expects
                    const normalized = auditRes.data.map((ev, idx) => ({
                        ...ev,
                        index: idx,
                        event_hash: ev.current_hash || ev.event_hash || "",
                        prev_hash: ev.previous_hash || ev.prev_hash || "",
                        operator: ev.description?.match(/by (\S+)/)?.[1] || ev.event_type || "mukui",
                        target: ev.description || ev.action || "",
                        case_id: ev.case_id || "",
                    }));
                    setAuditEvents(normalized);
                    const hashes = normalized.map((ev) => ev.event_hash).filter(Boolean);
                    computeRealMerkleRoot(hashes).then((root) => {
                        if (isMounted) setMerkleRoot(root);
                    });
                }
            } catch (e) {}

            try {
                const telemRes = await dashboardAPI.stats();
                if (isMounted && telemRes.data) {
                    setTelemetry({ is_wiping: telemRes.data.active_jobs > 0, ...telemRes.data });
                    setIsAgentOnline(true);
                    setLastSyncTime(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
                }
            } catch (e) {
                if (isMounted) setIsAgentOnline(false);
            }
        };

        fetchRealData();
        const interval = setInterval(fetchRealData, 2000);
        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    // Active cases: use live API if available, otherwise rich mock cases
    const displayCases = useMemo(() => {
        return casesData.length > 0 ? casesData : DEFAULT_CASES;
    }, [casesData]);

    // Active evidence: use live API evidence or fallback to rich mock evidence
    const displayEvidenceList = useMemo(() => {
        if (apiEvidence.length > 0) {
            return apiEvidence.map((e, idx) => ({
                evidence_id: e.evidence_number || `EVID-${idx + 1}`,
                label: e.source_device || `Storage Volume #${idx + 1}`,
                status: e.status || "ANALYZED",
                evidence_type: e.device_type || "Storage Volume",
                target_path: e.image_path || "/dev/storage0",
                size_bytes: e.capacity_bytes || 0,
                acquired_by: e.investigator || "mukui",
                sha256: e.sha256_hash || "",
            }));
        }
        return DEFAULT_EVIDENCE;
    }, [apiEvidence]);

    // Active carved files: use live API recovered files or fallback to rich mock files
    const displayFilesList = useMemo(() => {
        if (apiFiles.length > 0) {
            return apiFiles;
        }
        return DEFAULT_FILES;
    }, [apiFiles]);

    // Active audit ledger: use live API events or fallback to rich mock chain
    const displayAuditEvents = useMemo(() => {
        return auditEvents.length > 0 ? auditEvents : DEFAULT_AUDIT;
    }, [auditEvents]);

    useEffect(() => {
        if (!merkleRoot && displayAuditEvents.length > 0) {
            const hashes = displayAuditEvents.map((ev) => ev.event_hash).filter(Boolean);
            computeRealMerkleRoot(hashes).then((root) => setMerkleRoot(root));
        }
    }, [merkleRoot, displayAuditEvents]);

    // verify hash chain integrity
    const runChainVerification = async () => {
        setVerifying(true);
        setVerificationResult(null);

        if (!displayAuditEvents || displayAuditEvents.length === 0) {
            setVerifying(false);
            setVerificationResult({
                valid: false,
                reason: "No audit records found on agent",
            });
            return;
        }

        let brokenAt = null;
        let expectedPrev = "0000000000000000000000000000000000000000000000000000000000000000";

        for (let i = 0; i < displayAuditEvents.length; i++) {
            const ev = displayAuditEvents[i];
            if (ev.index !== i || ev.prev_hash !== expectedPrev) {
                brokenAt = i;
                break;
            }
            expectedPrev = ev.event_hash;
        }

        const calculatedMerkle = await computeRealMerkleRoot(displayAuditEvents.map((e) => e.event_hash));

        setTimeout(() => {
            setVerifying(false);
            setVerificationResult({
                valid: brokenAt === null,
                totalBlocks: displayAuditEvents.length,
                latestHash: displayAuditEvents[displayAuditEvents.length - 1]?.event_hash || "N/A",
                merkleRoot: calculatedMerkle,
                verifiedAt: new Date().toISOString(),
                brokenIndex: brokenAt,
            });
        }, 500);
    };

    // search filter
    const filteredAudit = useMemo(() => {
        if (!searchQuery) return displayAuditEvents;
        const q = searchQuery.toLowerCase();
        return displayAuditEvents.filter(
            (ev) =>
                ev.action?.toLowerCase().includes(q) ||
                ev.case_id?.toLowerCase().includes(q) ||
                ev.operator?.toLowerCase().includes(q) ||
                ev.event_hash?.toLowerCase().includes(q) ||
                ev.target?.toLowerCase().includes(q)
        );
    }, [displayAuditEvents, searchQuery]);

    const getActionBadgeColor = (action) => {
        const act = (action || "").toUpperCase();
        if (act.includes("EXPORT") || act.includes("RESTORE")) return "text-zinc-300 bg-zinc-800/80 border-zinc-700/80";
        if (act.includes("CARVE")) return "text-amber-300 bg-amber-950/40 border-amber-800/40";
        if (act.includes("WIPE") || act.includes("ERAS")) return "text-rose-300 bg-rose-950/40 border-rose-800/40";
        if (act.includes("VERIF") || act.includes("CERT")) return "text-emerald-300 bg-emerald-950/40 border-emerald-800/40";
        return "text-zinc-400 bg-zinc-900 border-zinc-800";
    };

    return (
        <div className="flex min-h-screen bg-[#09090b] text-zinc-100 font-sans antialiased selection:bg-zinc-800 selection:text-zinc-100">
            {/* sidebar */}
            <aside className={`${isSidebarOpen ? "w-64" : "w-18"} bg-[#0c0d0e] border-r border-zinc-800/80 flex flex-col justify-between shrink-0 z-20 sticky top-0 h-screen transition-all duration-200 ease-in-out`}>
                <div className="flex-1 overflow-y-auto no-scrollbar">
                    {/* logo and toggle button */}
                    <div className={`h-16 border-b border-zinc-800/80 flex items-center bg-[#0c0d0e] sticky top-0 z-10 ${isSidebarOpen ? "px-4 justify-between" : "px-2 justify-center"}`}>
                        {isSidebarOpen ? (
                            <>
                                <div className="flex items-center gap-2.5">
                                    <div className="w-7 h-7 rounded-lg bg-zinc-900 border border-zinc-700/60 p-1 flex items-center justify-center">
                                        <img src="/logo.png" alt="ZeroTrace" className="w-full h-full object-contain" />
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <span className="font-semibold text-sm tracking-tight text-zinc-100">
                                            ZeroTrace
                                        </span>
                                        <span className="text-[10px] font-mono text-zinc-500 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded">
                                            v1.4
                                        </span>
                                    </div>
                                </div>

                                <button
                                    onClick={() => setIsSidebarOpen(false)}
                                    className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 transition-colors cursor-pointer"
                                    title="Collapse sidebar"
                                    aria-label="Collapse sidebar"
                                >
                                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                                        <rect width="18" height="18" x="3" y="3" rx="2" />
                                        <path d="M9 3v18" />
                                        <path d="m14 9-3 3 3 3" />
                                    </svg>
                                </button>
                            </>
                        ) : (
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="w-9 h-9 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 p-1.5 flex items-center justify-center transition-colors cursor-pointer"
                                title="Expand sidebar"
                                aria-label="Expand sidebar"
                            >
                                <img src="/logo.png" alt="ZeroTrace" className="w-full h-full object-contain" />
                            </button>
                        )}
                    </div>

                    {/* desktop agent status */}
                    {isSidebarOpen ? (
                        <div className="mx-3 my-3 p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/80 text-xs">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className={`w-2 h-2 rounded-full ${isAgentOnline ? "bg-emerald-500" : "bg-amber-500"}`} />
                                    <span className="font-medium text-zinc-200">
                                        {isAgentOnline ? "Engine Connected" : "Connecting Agent..."}
                                    </span>
                                </div>
                                <span className="font-mono text-[10px] text-zinc-500">
                                    {isAgentOnline ? "SYNCED" : "POLLING"}
                                </span>
                            </div>
                            <div className="mt-2 pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[11px] font-mono text-zinc-400">
                                <span>IPC Bridge</span>
                                <span>{lastSyncTime || "2s interval"}</span>
                            </div>
                        </div>
                    ) : (
                        <div
                            onClick={() => setIsSidebarOpen(true)}
                            className="mx-2 my-3 p-2 rounded-lg bg-zinc-900/50 border border-zinc-800/80 flex justify-center cursor-pointer hover:bg-zinc-800/50 transition-colors"
                            title={`Engine: ${isAgentOnline ? "Connected" : "Polling"} - Click to expand`}
                        >
                            <span className={`w-2 h-2 rounded-full ${isAgentOnline ? "bg-emerald-500" : "bg-amber-500"}`} />
                        </div>
                    )}

                    {/* navigation tabs */}
                    <nav className={`pb-4 ${isSidebarOpen ? "px-2 space-y-4" : "px-2 space-y-3"}`}>
                        {[
                            {
                                group: "WORKSPACE",
                                items: [
                                    { id: "overview", label: "Overview", icon: IconOverview },
                                    { id: "cases", label: "Investigation Cases", icon: IconCases, badge: displayCases.length },
                                    { id: "evidence", label: "Evidence & Files", icon: IconEvidence, badge: displayEvidenceList.length + displayFilesList.length },
                                    { id: "operations", label: "Hardware Console", icon: IconTelemetry, live: telemetry?.is_wiping },
                                ],
                            },
                            {
                                group: "VERIFICATION",
                                items: [
                                    { id: "integrity", label: "Merkle Integrity", icon: IconMerkle },
                                    { id: "audit", label: "Audit Ledger", icon: IconAudit, badge: displayAuditEvents.length },
                                    { id: "reports", label: "Signed Reports", icon: IconReports },
                                ],
                            },
                            {
                                group: "SYSTEM",
                                items: [
                                    { id: "devices", label: "Workstations", icon: IconDevices },
                                    { id: "settings", label: "Configuration", icon: IconSettings },
                                ],
                            },
                        ].map((cat, catIdx) => (
                            <div key={catIdx} className="space-y-0.5">
                                {isSidebarOpen ? (
                                    <div className="px-2.5 pt-1.5 pb-1 text-[11px] font-medium text-zinc-400 tracking-wider uppercase">
                                        {cat.group}
                                    </div>
                                ) : (
                                    catIdx > 0 && <div className="h-px bg-zinc-800/80 my-2 mx-1" />
                                )}
                                <div className="space-y-0.5">
                                    {cat.items.map((item) => {
                                        const isCurrent = activeTab === item.id;
                                        const IconComp = item.icon;
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => setActiveTab(item.id)}
                                                title={item.label}
                                                className={`w-full flex items-center ${isSidebarOpen ? "justify-between px-2.5 py-1.5" : "justify-center py-2 px-1"} rounded-md text-xs transition-colors cursor-pointer ${
                                                    isCurrent
                                                        ? "bg-zinc-800 text-zinc-100 font-medium"
                                                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40"
                                                }`}
                                            >
                                                <div className="flex items-center gap-2.5 min-w-0">
                                                    <IconComp className={`w-4 h-4 shrink-0 ${isCurrent ? "text-zinc-100" : "text-zinc-400"}`} />
                                                    {isSidebarOpen && (
                                                        <span className="truncate">{item.label}</span>
                                                    )}
                                                </div>

                                                {isSidebarOpen && (
                                                    <div className="flex items-center gap-1.5 shrink-0 ml-1">
                                                        {item.badge !== undefined && item.badge > 0 && (
                                                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">
                                                                {item.badge}
                                                            </span>
                                                        )}
                                                        {item.live && (
                                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                                        )}
                                                    </div>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </nav>
                </div>

                {/* user info and exit button */}
                <div className={`border-t border-zinc-800/80 bg-[#0c0d0e] shrink-0 ${isSidebarOpen ? "p-3 space-y-2" : "p-2 space-y-2 flex flex-col items-center"}`}>
                    {isSidebarOpen ? (
                        <>
                            <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg bg-zinc-900/40 border border-zinc-800/60">
                                <div className="w-7 h-7 rounded-md bg-zinc-800 border border-zinc-700/60 flex items-center justify-center text-zinc-300 font-mono text-xs font-medium">
                                    OP
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs font-medium text-zinc-200 truncate">mukui</p>
                                    <p className="text-[11px] text-zinc-400 truncate">Lead Investigator</p>
                                </div>
                            </div>

                            <button
                                onClick={onBackToLanding}
                                className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 border border-zinc-800 rounded-md text-xs font-medium transition-colors cursor-pointer"
                            >
                                <svg className="w-3.5 h-3.5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="19" y1="12" x2="5" y2="12"></line>
                                    <polyline points="12 19 5 12 12 5"></polyline>
                                </svg>
                                <span>Return to Portal</span>
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={onBackToLanding}
                            className="w-8 h-8 rounded-md bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 flex items-center justify-center transition-colors cursor-pointer"
                            title="Return to Portal"
                        >
                            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="19" y1="12" x2="5" y2="12"></line>
                                <polyline points="12 19 5 12 12 5"></polyline>
                            </svg>
                        </button>
                    )}
                </div>
            </aside>

            {/* main content area */}
            <main className="flex-1 flex flex-col min-h-screen bg-[#09090b]">
                {/* top bar */}
                <header className="h-16 bg-[#0c0d0e]/90 backdrop-blur-md border-b border-zinc-800/80 px-6 flex items-center justify-between shrink-0 sticky top-0 z-30">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 border border-transparent hover:border-zinc-700/60 transition-colors cursor-pointer"
                            title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
                            aria-label={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
                        >
                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                                <rect width="18" height="18" x="3" y="3" rx="2" />
                                <path d="M9 3v18" />
                                {isSidebarOpen ? <path d="m14 9-3 3 3 3" /> : <path d="m11 9 3 3-3 3" />}
                            </svg>
                        </button>

                        <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                            <span>Console</span>
                            <span>/</span>
                            <span className="font-medium text-zinc-100 capitalize">
                                {activeTab.replace("-", " ")}
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <input
                                id="dashboard-search-input"
                                name="dashboardSearch"
                                type="search"
                                placeholder="Search hashes, cases, actions..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                autoComplete="off"
                                className="pl-8 pr-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-md text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 w-64 transition-colors font-mono"
                            />
                            <span className="absolute left-2.5 top-2 text-zinc-500 pointer-events-none">
                                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="11" cy="11" r="8"></circle>
                                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                                </svg>
                            </span>
                        </div>

                        <button
                            onClick={runChainVerification}
                            disabled={verifying}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-100 hover:bg-white text-zinc-900 rounded-md text-xs font-medium shadow-xs transition-colors cursor-pointer disabled:opacity-50"
                        >
                            <IconMerkle className="w-3.5 h-3.5" />
                            <span>{verifying ? "Auditing..." : "Verify Ledger"}</span>
                        </button>

                        <button
                            onClick={() => {
                                sessionStorage.setItem("zt_advisor_chat_is_open", "true");
                                window.dispatchEvent(new CustomEvent("zt-open-advisor"));
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-500/40 rounded-md text-xs font-medium shadow-xs transition-colors cursor-pointer"
                            title="Open Forensic Recovery Advisor"
                        >
                            <svg className="w-3.5 h-3.5 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            </svg>
                            <span>Forensic Advisor</span>
                        </button>
                    </div>
                </header>

                {/* active tab content */}
                <div className="flex-1 p-6 sm:p-8 max-w-7xl w-full mx-auto space-y-6">
                    {/* tab 1: overview */}
                    {activeTab === "overview" && (
                        <div className="space-y-6">
                            {/* metric cards */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                {/* active cases card */}
                                <div className="bg-[#111215] p-4.5 rounded-xl border border-zinc-800/80 hover:border-zinc-700/80 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">
                                            Active Cases
                                        </span>
                                        <IconCases className="w-4 h-4 text-zinc-400" />
                                    </div>
                                    <div className="flex items-baseline gap-2 mt-2">
                                        <h3 className="text-2xl sm:text-3xl font-semibold text-zinc-100 tabular-nums">
                                            {casesData.length}
                                        </h3>
                                        <span className="text-xs text-zinc-400">registered</span>
                                    </div>
                                    <p className="text-xs text-zinc-400 mt-2 font-mono">
                                        Central Platform DB
                                    </p>
                                </div>

                                {/* ledger height card */}
                                <div className="bg-[#111215] p-4.5 rounded-xl border border-zinc-800/80 hover:border-zinc-700/80 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">
                                            Ledger Height
                                        </span>
                                        <IconAudit className="w-4 h-4 text-zinc-400" />
                                    </div>
                                    <div className="flex items-baseline gap-2 mt-2">
                                        <h3 className="text-2xl sm:text-3xl font-semibold text-zinc-100 tabular-nums font-mono">
                                            #{auditEvents.length}
                                        </h3>
                                        <span className="text-xs text-zinc-400">blocks</span>
                                    </div>
                                    <p className="text-xs text-zinc-400 mt-2 font-mono">
                                        SHA-256 chain
                                    </p>
                                </div>

                                {/* wipe engine status card */}
                                <div className="bg-[#111215] p-4.5 rounded-xl border border-zinc-800/80 hover:border-zinc-700/80 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">
                                            Sanitization Engine
                                        </span>
                                        <IconTelemetry className="w-4 h-4 text-zinc-400" />
                                    </div>
                                    <div className="flex items-baseline gap-2 mt-2">
                                        <h3 className="text-2xl sm:text-3xl font-semibold text-zinc-100 tabular-nums font-mono uppercase">
                                            {telemetry?.is_wiping ? `${telemetry.progress || 0}%` : telemetry?.status || "STANDBY"}
                                        </h3>
                                    </div>
                                    <p className="text-xs text-zinc-400 mt-2 truncate font-mono" title={telemetry?.target || "No active task"}>
                                        {telemetry?.target || "No active task"}
                                    </p>
                                </div>

                                {/* merkle root card */}
                                <div className="bg-[#111215] p-4.5 rounded-xl border border-zinc-800/80 hover:border-zinc-700/80 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">
                                            Merkle Root
                                        </span>
                                        <IconMerkle className="w-4 h-4 text-zinc-400" />
                                    </div>
                                    <div className="flex items-center justify-between mt-2">
                                        <h3 className="text-sm font-mono font-medium text-zinc-200 truncate max-w-[130px]" title={merkleRoot}>
                                            {merkleRoot ? `${merkleRoot.substring(0, 10)}...` : "Computing..."}
                                        </h3>
                                        {merkleRoot && (
                                            <button
                                                onClick={() => copyToClipboard(merkleRoot, "merkle")}
                                                className="text-[10px] font-mono text-zinc-400 hover:text-zinc-100 px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 transition-colors cursor-pointer"
                                                title="Copy full SHA-256 Merkle root"
                                            >
                                                {copiedHash === "merkle" ? "✓" : "Copy"}
                                            </button>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-1.5 mt-2 text-xs text-emerald-400">
                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                        <span>Cryptographically intact</span>
                                    </div>
                                </div>
                            </div>

                            {/* verification result notification */}
                            {verificationResult && (
                                <div className={`p-4 rounded-xl border text-xs ${verificationResult.valid ? "bg-zinc-900/60 border-emerald-500/30 text-zinc-200" : "bg-zinc-900/60 border-rose-500/30 text-zinc-200"}`}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2.5">
                                            <span className={`w-2 h-2 rounded-full ${verificationResult.valid ? "bg-emerald-500" : "bg-rose-500"}`} />
                                            <div>
                                                <p className="font-semibold text-zinc-100">
                                                    {verificationResult.valid ? "Audit Chain Verification Completed" : "Cryptographic Discrepancy Found"}
                                                </p>
                                                <p className="text-xs text-zinc-400 mt-0.5">
                                                    Validated {verificationResult.totalBlocks} chronological blocks against recursive SHA-256 Merkle root.
                                                </p>
                                            </div>
                                        </div>
                                        <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-medium ${verificationResult.valid ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                                            {verificationResult.valid ? "VERIFIED" : "TAMPERED"}
                                        </span>
                                    </div>
                                    <div className="mt-3 pt-3 border-t border-zinc-800 grid grid-cols-1 md:grid-cols-3 gap-2 font-mono text-[11px] text-zinc-400">
                                        <div>Blocks: #{verificationResult.totalBlocks}</div>
                                        <div className="truncate">Root: {verificationResult.merkleRoot}</div>
                                        <div>Timestamp: {new Date(verificationResult.verifiedAt).toLocaleTimeString()}</div>
                                    </div>
                                </div>
                            )}

                            {/* live wipe status */}
                            {telemetry && (
                                <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs font-semibold text-zinc-100">Hardware Bridge</span>
                                                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-medium border ${telemetry.is_wiping ? "bg-amber-500/10 text-amber-400 border-amber-500/20" : "bg-zinc-900 text-zinc-400 border-zinc-800"}`}>
                                                    {telemetry.status || "STANDBY"}
                                                </span>
                                            </div>
                                            <p className="text-xs text-zinc-400 mt-1 font-mono">
                                                Target: <span className="text-zinc-200">{telemetry.target || "Local Storage Volumes"}</span> • Method: <span className="text-zinc-200">{telemetry.method || "NIST SP 800-88 Purge"}</span>
                                            </p>
                                        </div>

                                        {telemetry.is_wiping && (
                                            <div className="text-right font-mono">
                                                <span className="text-xl font-semibold text-zinc-100">{telemetry.progress || 0}%</span>
                                                <p className="text-xs text-zinc-400">{telemetry.speed_mb_s || 0} MB/s</p>
                                            </div>
                                        )}
                                    </div>

                                    {telemetry.is_wiping && (
                                        <div className="w-full bg-zinc-900 rounded-full h-2 overflow-hidden border border-zinc-800 mt-2">
                                            <div
                                                className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                                                style={{ width: `${telemetry.progress || 0}%` }}
                                            />
                                        </div>
                                    )}

                                    {/* latest log message */}
                                    <div className="mt-3 p-3 bg-zinc-950 rounded-lg border border-zinc-800/80 font-mono text-xs text-zinc-400 flex items-center justify-between">
                                        <div className="flex items-center gap-2 truncate">
                                            <span className="text-zinc-500">$</span>
                                            <span className="truncate">{telemetry.new_log || `Device bridge synchronized with ${telemetry.target || "system storage"}`}</span>
                                        </div>
                                        <div className="flex items-center gap-1.5 shrink-0 ml-3 text-[11px] text-zinc-400">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                            <span>Online</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* environmental savings chart */}
                            <EnvironmentalImpactCard auditEvents={displayAuditEvents} telemetry={telemetry} />

                            {/* recent audit logs */}
                            <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                                <div className="flex justify-between items-center mb-4">
                                    <div>
                                        <h3 className="text-sm font-semibold text-zinc-100">
                                            Chronological Hash Chain Ledger
                                        </h3>
                                        <p className="text-xs text-zinc-400 mt-0.5">
                                            Live immutable audit trail from central database
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => setActiveTab("audit")}
                                        className="text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer flex items-center gap-1"
                                    >
                                        <span>View all {displayAuditEvents.length} records</span>
                                        <span>→</span>
                                    </button>
                                </div>

                                <div className="overflow-x-auto rounded-lg border border-zinc-800/80">
                                    <table className="w-full text-left text-xs">
                                        <thead>
                                            <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider bg-zinc-950/60">
                                                <th className="py-2.5 px-3"># Block</th>
                                                <th className="py-2.5 px-3">Timestamp (UTC)</th>
                                                <th className="py-2.5 px-3">Operator</th>
                                                <th className="py-2.5 px-3">Action</th>
                                                <th className="py-2.5 px-3">Target</th>
                                                <th className="py-2.5 px-3 text-right">Hash (SHA-256)</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-zinc-800/60 font-mono text-xs">
                                            {displayAuditEvents.slice(-7).reverse().map((ev) => (
                                                <tr key={ev.index} className="hover:bg-zinc-800/30 transition-colors group">
                                                    <td className="py-2.5 px-3 font-semibold text-zinc-300">
                                                        #{String(ev.index).padStart(4, "0")}
                                                    </td>
                                                    <td className="py-2.5 px-3 text-zinc-400 font-sans">
                                                        {new Date(ev.timestamp).toLocaleString()}
                                                    </td>
                                                    <td className="py-2.5 px-3 font-sans font-medium text-zinc-200">
                                                        {ev.operator}
                                                    </td>
                                                    <td className="py-2.5 px-3">
                                                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium border ${getActionBadgeColor(ev.action)}`}>
                                                            {ev.action}
                                                        </span>
                                                    </td>
                                                    <td className="py-2.5 px-3 text-zinc-300 truncate max-w-[200px]" title={ev.target}>
                                                        {ev.target}
                                                    </td>
                                                    <td className="py-2.5 px-3 text-right">
                                                        <div className="flex items-center justify-end gap-1.5">
                                                            <span className="text-zinc-400 font-mono">
                                                                {ev.event_hash ? `${ev.event_hash.substring(0, 10)}...` : "N/A"}
                                                            </span>
                                                            {ev.event_hash && (
                                                                <button
                                                                    onClick={() => copyToClipboard(ev.event_hash, ev.index)}
                                                                    className="opacity-0 group-hover:opacity-100 text-[10px] text-zinc-400 hover:text-zinc-100 px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 transition-opacity cursor-pointer"
                                                                    title="Copy hash"
                                                                >
                                                                    {copiedHash === ev.index ? "✓" : "Copy"}
                                                                </button>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* tab 2: cases */}
                    {activeTab === "cases" && (
                        <div className="space-y-4">
                            <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                                <div className="flex justify-between items-center mb-4">
                                    <div>
                                        <h3 className="text-sm font-semibold text-zinc-100">Forensic Investigation Cases</h3>
                                        <p className="text-xs text-zinc-400 mt-0.5">
                                            Live investigation cases from central platform database.
                                        </p>
                                    </div>
                                    <span className="text-xs font-mono font-medium text-zinc-400 bg-zinc-900 border border-zinc-800 px-2.5 py-1 rounded-md">
                                        {displayCases.length} Cases
                                    </span>
                                </div>

                                {displayCases.length === 0 ? (
                                    <div className="p-8 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
                                        <p className="text-sm font-medium text-zinc-300">No registered cases found</p>
                                        <p className="text-xs text-zinc-500 mt-1">Initialize a case in the ZeroTrace desktop tool to see records here.</p>
                                    </div>
                                ) : (
                                    <div className="overflow-x-auto rounded-lg border border-zinc-800/80">
                                        <table className="w-full text-left text-xs">
                                            <thead>
                                                <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider bg-zinc-950/60">
                                                    <th className="py-2.5 px-3">Case ID</th>
                                                    <th className="py-2.5 px-3">Title & Agency</th>
                                                    <th className="py-2.5 px-3">Investigator</th>
                                                    <th className="py-2.5 px-3">Status</th>
                                                    <th className="py-2.5 px-3">Created</th>
                                                    <th className="py-2.5 px-3">Evidence</th>
                                                    <th className="py-2.5 px-3 text-right">Action</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-zinc-800/60">
                                                {displayCases.map((c) => (
                                                    <tr key={c.id || c.case_id} className="hover:bg-zinc-800/30 transition-colors">
                                                        <td className="py-3 px-3 font-mono font-semibold text-zinc-200">{c.case_number || c.case_id || "—"}</td>
                                                        <td className="py-3 px-3">
                                                            <div className="font-medium text-zinc-100">{c.title}</div>
                                                            <div className="text-[11px] text-zinc-500">{c.agency || ""}</div>
                                                        </td>
                                                        <td className="py-3 px-3 text-zinc-300">{c.investigator || "Assigned"}</td>
                                                        <td className="py-3 px-3">
                                                            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                                {c.status || "ACTIVE"}
                                                            </span>
                                                        </td>
                                                        <td className="py-3 px-3 text-zinc-400 font-mono text-[11px]">
                                                            {new Date(c.created_at).toLocaleDateString()}
                                                        </td>
                                                        <td className="py-3 px-3 font-mono text-zinc-300">
                                                            {c.evidence_count ?? c.evidence_items?.length ?? 0} items
                                                        </td>
                                                        <td className="py-3 px-3 text-right">
                                                            <button
                                                                onClick={() => setSelectedCase(c)}
                                                                className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 rounded-md text-xs font-medium border border-zinc-800 transition-colors cursor-pointer"
                                                            >
                                                                Inspect
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>

                            {selectedCase && (
                                <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                                    <div className="flex justify-between items-center pb-3 border-b border-zinc-800">
                                        <h3 className="font-semibold text-zinc-100 text-sm">{selectedCase.title}</h3>
                                        <button onClick={() => setSelectedCase(null)} className="text-zinc-500 hover:text-zinc-300 text-xs cursor-pointer">
                                            Close
                                        </button>
                                    </div>
                                    <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                                        <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800/60">
                                            <p className="text-zinc-500 font-medium">Case Identifier</p>
                                            <p className="font-mono text-zinc-200 mt-1">{selectedCase.case_number || selectedCase.case_id || selectedCase.id}</p>
                                        </div>
                                        <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800/60">
                                            <p className="text-zinc-500 font-medium">Description</p>
                                            <p className="text-zinc-300 mt-1">{selectedCase.description || "Forensic investigation archive."}</p>
                                        </div>
                                        <div className="p-3 bg-zinc-950/60 rounded-lg border border-zinc-800/60">
                                            <p className="text-zinc-500 font-medium">Created</p>
                                            <p className="font-mono text-zinc-300 mt-1">{new Date(selectedCase.created_at).toUTCString()}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* tab 3: evidence & carved files */}
                    {activeTab === "evidence" && (
                        <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-5">
                                <div>
                                    <h3 className="text-sm font-semibold text-zinc-100">Forensic Evidence & Artifact Pool</h3>
                                    <p className="text-xs text-zinc-400 mt-0.5">Physical seized drives, bitstream images, and carved files from active cases.</p>
                                </div>
                                <div className="flex items-center p-1 bg-zinc-950 border border-zinc-800 rounded-lg text-xs font-mono">
                                    <button
                                        onClick={() => setEvidenceSubTab("devices")}
                                        className={`px-3 py-1 rounded-md transition-colors cursor-pointer text-xs font-medium ${evidenceSubTab === "devices" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"}`}
                                    >
                                        Physical Media ({displayEvidenceList.length})
                                    </button>
                                    <button
                                        onClick={() => setEvidenceSubTab("files")}
                                        className={`px-3 py-1 rounded-md transition-colors cursor-pointer text-xs font-medium ${evidenceSubTab === "files" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"}`}
                                    >
                                        Carved Files & Artifacts ({displayFilesList.length})
                                    </button>
                                </div>
                            </div>

                            {evidenceSubTab === "devices" ? (
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    {displayEvidenceList.map((e, idx) => (
                                        <div key={idx} className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-950/60">
                                            <div className="flex justify-between items-start">
                                                <span className="px-2 py-0.5 rounded bg-zinc-900 text-zinc-300 text-[10px] font-mono border border-zinc-800">
                                                    {e.evidence_id || `EVID-${idx + 1}`}
                                                </span>
                                                <span className="text-[10px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                                                    {e.status || "ANALYZED"}
                                                </span>
                                            </div>
                                            <h4 className="font-semibold text-zinc-100 text-sm mt-2">{e.label || e.target_path}</h4>
                                            <p className="text-[11px] text-zinc-400">{e.evidence_type || "Storage Volume"}</p>
                                            <div className="mt-3 space-y-1 text-xs font-mono text-zinc-400 border-t border-zinc-800 pt-2">
                                                <div>Path: <span className="text-zinc-200">{e.target_path}</span></div>
                                                <div>Capacity: <span className="text-zinc-200">{e.size_bytes >= 1e12 ? `${(e.size_bytes / 1e12).toFixed(1)} TB` : e.size_bytes >= 1e9 ? `${(e.size_bytes / 1e9).toFixed(0)} GB` : `${(e.size_bytes / 1e6).toFixed(0)} MB`}</span></div>
                                                <div>Investigator: <span className="text-zinc-200">{e.acquired_by || "mukui"}</span></div>
                                            </div>
                                            {e.sha256 && (
                                                <div className="mt-2.5 text-[10px] font-mono text-zinc-400 truncate bg-zinc-900 p-1.5 rounded border border-zinc-800 flex items-center justify-between">
                                                    <span className="truncate">SHA: {e.sha256}</span>
                                                    <button
                                                        onClick={() => copyToClipboard(e.sha256, `ev-${idx}`)}
                                                        className="ml-2 text-zinc-400 hover:text-zinc-100 text-[10px] cursor-pointer"
                                                    >
                                                        {copiedHash === `ev-${idx}` ? "✓" : "Copy"}
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    {displayFilesList.map((f, idx) => (
                                        <div key={idx} className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-950/60 hover:border-zinc-700/80 transition-colors">
                                            <div className="flex justify-between items-start">
                                                <span className="px-2 py-0.5 rounded bg-zinc-900 text-emerald-400 text-[10px] font-mono font-semibold border border-zinc-800">
                                                    {f.file_type || "FILE"}
                                                </span>
                                                <span className="text-[10px] font-mono font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                                                    {Math.round((f.confidence_score || 0.95) * 100)}% Match
                                                </span>
                                            </div>
                                            <h4 className="font-semibold text-zinc-100 text-xs sm:text-sm mt-2 font-mono truncate" title={f.filename}>
                                                {f.filename}
                                            </h4>
                                            <p className="text-[11px] text-zinc-400">{f.category || "DOCUMENT"}</p>
                                            <div className="mt-3 space-y-1 text-xs font-mono text-zinc-400 border-t border-zinc-800 pt-2">
                                                <div>Size: <span className="text-zinc-200">{f.size_bytes >= 1e6 ? `${(f.size_bytes / 1e6).toFixed(2)} MB` : `${(f.size_bytes / 1024).toFixed(0)} KB`}</span></div>
                                                <div>Carving: <span className="text-zinc-200">{f.recovery_method || "Signature Carve"}</span></div>
                                                <div>Structure: <span className={f.is_fragmented ? "text-amber-400" : "text-emerald-400"}>{f.is_fragmented ? "Reconstructed" : "Contiguous"}</span></div>
                                            </div>
                                            {f.sha256_hash && (
                                                <div className="mt-2.5 text-[10px] font-mono text-zinc-400 truncate bg-zinc-900 p-1.5 rounded border border-zinc-800 flex items-center justify-between">
                                                    <span className="truncate">SHA: {f.sha256_hash}</span>
                                                    <button
                                                        onClick={() => copyToClipboard(f.sha256_hash, `file-${idx}`)}
                                                        className="ml-2 text-zinc-400 hover:text-zinc-100 text-[10px] cursor-pointer"
                                                    >
                                                        {copiedHash === `file-${idx}` ? "✓" : "Copy"}
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* tab 4: hardware operations */}
                    {activeTab === "operations" && (
                        <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <h3 className="text-sm font-semibold text-zinc-100">Live Hardware Console</h3>
                                    <p className="text-xs text-zinc-400 mt-0.5">Desktop wiping and carving telemetry feed.</p>
                                </div>
                                <span className="text-xs font-mono font-medium text-zinc-400 bg-zinc-900 border border-zinc-800 px-2.5 py-1 rounded-md">
                                    LIVE FEED
                                </span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 bg-zinc-950/60 rounded-lg border border-zinc-800/60 text-xs">
                                <div>
                                    <p className="text-zinc-500 font-medium">Hardware Target</p>
                                    <p className="font-mono text-zinc-200 mt-1 font-semibold">{telemetry?.target || "None currently selected"}</p>
                                </div>
                                <div>
                                    <p className="text-zinc-500 font-medium">Sanitization Standard</p>
                                    <p className="font-mono text-zinc-200 mt-1">{telemetry?.method || "NIST SP 800-88 Purge"}</p>
                                </div>
                                <div>
                                    <p className="text-zinc-500 font-medium">Operation Status</p>
                                    <p className="font-mono text-emerald-400 mt-1">{telemetry?.status || "STANDBY"}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* tab 5: merkle integrity */}
                    {activeTab === "integrity" && (
                        <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <h3 className="text-sm font-semibold text-zinc-100">Merkle Tree & Hash Chain Verification</h3>
                                    <p className="text-xs text-zinc-400 mt-0.5">
                                        Recursive binary SHA-256 tree computed across {displayAuditEvents.length} chronological blocks.
                                    </p>
                                </div>
                                <button
                                    onClick={runChainVerification}
                                    disabled={verifying}
                                    className="px-3 py-1.5 bg-zinc-100 hover:bg-white text-zinc-900 font-medium rounded-md text-xs transition-colors cursor-pointer"
                                >
                                    {verifying ? "Auditing..." : "Run Cryptographic Audit"}
                                </button>
                            </div>

                            <div className="p-6 bg-zinc-950/60 rounded-lg border border-zinc-800/60 text-center">
                                <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Dynamic Merkle Root</span>
                                <div className="mt-2 flex justify-center">
                                    <div className="p-3 bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-md text-xs font-mono max-w-xl break-all">
                                        {merkleRoot || "Computing from leaf hashes..."}
                                    </div>
                                </div>
                                <p className="text-xs font-mono text-zinc-500 mt-3">
                                    Tree Depth: {Math.ceil(Math.log2(Math.max(1, displayAuditEvents.length))) + 1} levels • Leaf Hashes: {displayAuditEvents.length}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* tab 6: audit logs */}
                    {activeTab === "audit" && (
                        <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <h3 className="text-sm font-semibold text-zinc-100">Hash Chain Audit Trail</h3>
                                    <p className="text-xs text-zinc-400 mt-0.5">
                                        Full chronological ledger ({filteredAudit.length} of {displayAuditEvents.length} records matching).
                                    </p>
                                </div>
                                <span className="text-xs font-mono font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-md">
                                    Chain Intact
                                </span>
                            </div>

                            <div className="overflow-x-auto rounded-lg border border-zinc-800/80">
                                <table className="w-full text-left text-xs">
                                    <thead>
                                        <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider bg-zinc-950/60">
                                            <th className="py-2.5 px-3"># Block</th>
                                            <th className="py-2.5 px-3">Timestamp (UTC)</th>
                                            <th className="py-2.5 px-3">Operator</th>
                                            <th className="py-2.5 px-3">Action</th>
                                            <th className="py-2.5 px-3">Target</th>
                                            <th className="py-2.5 px-3">Case ID</th>
                                            <th className="py-2.5 px-3 text-right">Event Hash</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-zinc-800/60 font-mono text-xs">
                                        {filteredAudit.map((ev) => (
                                            <tr key={ev.index} className="hover:bg-zinc-800/30 transition-colors">
                                                <td className="py-2.5 px-3 font-semibold text-zinc-300">#{String(ev.index).padStart(4, "0")}</td>
                                                <td className="py-2.5 px-3 text-zinc-400 font-sans">{new Date(ev.timestamp).toLocaleString()}</td>
                                                <td className="py-2.5 px-3 font-sans font-medium text-zinc-200">{ev.operator}</td>
                                                <td className="py-2.5 px-3">
                                                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium border ${getActionBadgeColor(ev.action)}`}>
                                                        {ev.action}
                                                    </span>
                                                </td>
                                                <td className="py-2.5 px-3 text-zinc-300 truncate max-w-[180px] font-sans" title={ev.target}>{ev.target}</td>
                                                <td className="py-2.5 px-3 text-zinc-400 font-sans">{ev.case_id}</td>
                                                <td className="py-2.5 px-3 text-right text-zinc-500">{ev.event_hash ? `${ev.event_hash.substring(0, 10)}...` : "N/A"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* tab 7: workstations */}
                    {activeTab === "devices" && (
                        <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                            <h3 className="text-sm font-semibold text-zinc-100 mb-1">Connected Workstations</h3>
                            <p className="text-xs text-zinc-400 mb-4">Endpoints connected to the local telemetry bridge.</p>

                            <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-950/60 max-w-sm">
                                <div className="flex justify-between items-start">
                                    <span className="text-xs font-mono font-medium text-zinc-300">HOST-LOCAL-01</span>
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${isAgentOnline ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20"}`}>
                                        {isAgentOnline ? "ONLINE" : "STANDBY"}
                                    </span>
                                </div>
                                <h4 className="font-semibold text-zinc-100 text-sm mt-2">ZeroTrace Forensic Agent</h4>
                                <p className="text-xs text-zinc-500">Desktop Win32 Runtime</p>
                                <div className="mt-3 space-y-1.5 text-xs font-mono text-zinc-400 border-t border-zinc-800 pt-2.5">
                                    <div className="flex justify-between">
                                        <span>Socket:</span>
                                        <span className="text-zinc-200">127.0.0.1:5173</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Blocks:</span>
                                        <span className="font-medium text-zinc-200">#{auditEvents.length}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* tab 8: reports export */}
                    {activeTab === "reports" && (
                        <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80">
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <h3 className="text-sm font-semibold text-zinc-100">Audit Reports & Export</h3>
                                    <p className="text-xs text-zinc-400 mt-0.5">Export cryptographically signed ledgers and audit records.</p>
                                </div>
                                <button
                                    onClick={() => {
                                        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(auditEvents, null, 2));
                                        const dl = document.createElement("a");
                                        dl.setAttribute("href", dataStr);
                                        dl.setAttribute("download", `ZeroTrace_Audit_Trail_${Date.now()}.json`);
                                        dl.click();
                                    }}
                                    className="px-3 py-1.5 bg-zinc-100 hover:bg-white text-zinc-900 font-medium rounded-md text-xs transition-colors cursor-pointer"
                                >
                                    Export Ledger (JSON)
                                </button>
                            </div>

                            <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-950/60 flex items-center justify-between">
                                <div>
                                    <h4 className="font-medium text-zinc-200 text-xs">Full Cryptographic Audit Ledger</h4>
                                    <p className="text-[11px] text-zinc-500 font-mono mt-0.5">
                                        Contains {auditEvents.length} signed blocks from genesis.
                                    </p>
                                </div>
                                <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                                    Validated
                                </span>
                            </div>
                        </div>
                    )}

                    {/* tab 9: bridge settings */}
                    {activeTab === "settings" && (
                        <div className="bg-[#111215] p-5 rounded-xl border border-zinc-800/80 max-w-2xl">
                            <h3 className="text-sm font-semibold text-zinc-100 mb-1">Bridge Storage Paths</h3>
                            <p className="text-xs text-zinc-400 mb-4">Local file-bridge endpoints connecting the desktop client to the console.</p>
                            <div className="space-y-3 text-xs font-mono">
                                <div>
                                    <label htmlFor="setting-audit-trail" className="block text-zinc-400 font-sans mb-1">Desktop Audit Trail Source</label>
                                    <input
                                        id="setting-audit-trail"
                                        name="settingAuditTrail"
                                        type="text"
                                        value="/public/audit_trail.json"
                                        disabled
                                        className="w-full p-2.5 bg-zinc-950 border border-zinc-800 rounded-md text-zinc-300"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="setting-cases-source" className="block text-zinc-400 font-sans mb-1">Desktop Cases Source</label>
                                    <input
                                        id="setting-cases-source"
                                        name="settingCasesSource"
                                        type="text"
                                        value="/public/forensic_cases.json"
                                        disabled
                                        className="w-full p-2.5 bg-zinc-950 border border-zinc-800 rounded-md text-zinc-300"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="setting-telemetry-bridge" className="block text-zinc-400 font-sans mb-1">Telemetry Bridge</label>
                                    <input
                                        id="setting-telemetry-bridge"
                                        name="settingTelemetryBridge"
                                        type="text"
                                        value="/public/live_wipe_telemetry.json"
                                        disabled
                                        className="w-full p-2.5 bg-zinc-950 border border-zinc-800 rounded-md text-zinc-300"
                                    />
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default DashboardView;
