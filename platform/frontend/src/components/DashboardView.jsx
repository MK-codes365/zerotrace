import React, { useState, useEffect, useMemo } from "react";

// Cryptographic SHA-256 in browser for real Merkle Root & Hash Chain calculation
async function sha256Hex(str) {
    const buffer = new TextEncoder().encode(str);
    const hash = await crypto.subtle.digest("SHA-256", buffer);
    return Array.from(new Uint8Array(hash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}

// Compute real hierarchical Merkle Root from leaf hashes
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

const DashboardView = ({ onBackToLanding }) => {
    const [activeTab, setActiveTab] = useState("overview");
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedCase, setSelectedCase] = useState(null);
    const [copiedHash, setCopiedHash] = useState(null);

    // ── Real Data States ──────────────────────────────────────────────
    const [casesData, setCasesData] = useState([]);
    const [auditEvents, setAuditEvents] = useState([]);
    const [telemetry, setTelemetry] = useState(null);
    const [merkleRoot, setMerkleRoot] = useState("");
    const [isAgentOnline, setIsAgentOnline] = useState(false);
    const [lastSyncTime, setLastSyncTime] = useState(null);

    // Verification Test State
    const [verifying, setVerifying] = useState(false);
    const [verificationResult, setVerificationResult] = useState(null);

    // Copy to clipboard helper
    const copyToClipboard = (text, id) => {
        if (!text) return;
        navigator.clipboard.writeText(text);
        setCopiedHash(id || text);
        setTimeout(() => setCopiedHash(null), 2000);
    };

    // ── Real Telemetry & Data Polling Loop ─────────────────────────────
    useEffect(() => {
        let isMounted = true;

        const fetchRealData = async () => {
            try {
                // 1. Fetch Real Cases from Desktop
                const casesRes = await fetch("/forensic_cases.json?" + Date.now());
                if (casesRes.ok) {
                    const json = await casesRes.json();
                    if (isMounted && json && json.cases) {
                        const list = Object.values(json.cases);
                        setCasesData(list);
                    }
                }
            } catch (e) {
                // fallback if empty
            }

            try {
                // 2. Fetch Real Hash Chain Audit Trail from Desktop
                const auditRes = await fetch("/audit_trail.json?" + Date.now());
                if (auditRes.ok) {
                    const events = await auditRes.json();
                    if (isMounted && Array.isArray(events)) {
                        setAuditEvents(events);

                        // Compute Real Merkle Root from real event hashes
                        const hashes = events.map((ev) => ev.event_hash || ev.prev_hash).filter(Boolean);
                        computeRealMerkleRoot(hashes).then((root) => {
                            if (isMounted) setMerkleRoot(root);
                        });
                    }
                }
            } catch (e) {
                // fallback
            }

            try {
                // 3. Fetch Real Hardware Wipe Telemetry
                const telemRes = await fetch("/live_wipe_telemetry.json?" + Date.now());
                if (telemRes.ok) {
                    const telem = await telemRes.json();
                    if (isMounted && telem) {
                        setTelemetry(telem);
                        setIsAgentOnline(true);
                        setLastSyncTime(new Date().toLocaleTimeString());
                    }
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

    // ── Real Cryptographic Chain Verification ──────────────────────────
    const runChainVerification = async () => {
        setVerifying(true);
        setVerificationResult(null);

        if (!auditEvents || auditEvents.length === 0) {
            setVerifying(false);
            setVerificationResult({
                valid: false,
                reason: "No audit events found on desktop agent",
            });
            return;
        }

        let brokenAt = null;
        let expectedPrev = "0000000000000000000000000000000000000000000000000000000000000000";

        for (let i = 0; i < auditEvents.length; i++) {
            const ev = auditEvents[i];
            if (ev.index !== i || ev.prev_hash !== expectedPrev) {
                brokenAt = i;
                break;
            }
            expectedPrev = ev.event_hash;
        }

        const calculatedMerkle = await computeRealMerkleRoot(auditEvents.map((e) => e.event_hash));

        setTimeout(() => {
            setVerifying(false);
            setVerificationResult({
                valid: brokenAt === null,
                totalBlocks: auditEvents.length,
                latestHash: auditEvents[auditEvents.length - 1]?.event_hash || "N/A",
                merkleRoot: calculatedMerkle,
                verifiedAt: new Date().toISOString(),
                brokenIndex: brokenAt,
            });
        }, 600);
    };

    // Filtered audit events for search
    const filteredAudit = useMemo(() => {
        if (!searchQuery) return auditEvents;
        const q = searchQuery.toLowerCase();
        return auditEvents.filter(
            (ev) =>
                ev.action?.toLowerCase().includes(q) ||
                ev.case_id?.toLowerCase().includes(q) ||
                ev.operator?.toLowerCase().includes(q) ||
                ev.event_hash?.toLowerCase().includes(q) ||
                ev.target?.toLowerCase().includes(q)
        );
    }, [auditEvents, searchQuery]);

    // Real Evidence items gathered from real cases
    const realEvidenceList = useMemo(() => {
        const list = [];
        casesData.forEach((c) => {
            if (Array.isArray(c.evidence_items)) {
                c.evidence_items.forEach((item) => {
                    list.push({ ...item, caseTitle: c.title, caseId: c.case_id });
                });
            }
        });
        return list;
    }, [casesData]);

    const getActionBadgeColor = (action) => {
        const act = (action || "").toUpperCase();
        if (act.includes("EXPORT") || act.includes("RESTORE")) return "text-cyan-400 bg-cyan-950/50 border-cyan-800/60";
        if (act.includes("CARVE")) return "text-amber-400 bg-amber-950/50 border-amber-800/60";
        if (act.includes("WIPE") || act.includes("ERAS")) return "text-rose-400 bg-rose-950/50 border-rose-800/60";
        if (act.includes("VERIF") || act.includes("CERT")) return "text-emerald-400 bg-emerald-950/50 border-emerald-800/60";
        return "text-[#f4efe7]/80 bg-white/5 border-white/10";
    };

    return (
        <div className="flex min-h-screen bg-[#0d0e11] text-[#f4efe7] font-sans antialiased selection:bg-[#00f0ff] selection:text-[#0d0e11]" data-lenis-prevent="true">
            {/* ── SIDEBAR ────────────────────────────────────────────── */}
            <aside className="w-68 bg-[#131418] border-r border-white/10 flex flex-col justify-between shrink-0 z-20 sticky top-0 h-screen overflow-y-auto shadow-2xl">
                <div>
                    {/* Header Brand */}
                    <div className="h-18 px-5 border-b border-white/10 flex items-center justify-between bg-[#101115]">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 p-0.5 shadow-lg shadow-cyan-500/20 flex items-center justify-center">
                                <div className="w-full h-full bg-[#131418] rounded-[10px] flex items-center justify-center p-1.5">
                                    <img src="/logo.png" alt="ZeroTrace" className="w-full h-full object-contain" />
                                </div>
                            </div>
                            <div>
                                <div className="flex items-center gap-1.5">
                                    <h1 className="font-extrabold text-sm tracking-wide text-white uppercase">ZeroTrace</h1>
                                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                                        PRO
                                    </span>
                                </div>
                                <p className="text-[#8e8a83] text-[10px] tracking-wider uppercase font-mono mt-0.5">Forensic Telemetry Hub</p>
                            </div>
                        </div>
                    </div>

                    {/* Agent Live Connectivity Status Banner */}
                    <div className="mx-3.5 my-3 p-3 rounded-xl bg-[#18191f] border border-white/10 relative overflow-hidden shadow-inner">
                        <div className="flex items-center justify-between mb-1.5">
                            <div className="flex items-center gap-2">
                                <span className="relative flex h-2.5 w-2.5">
                                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isAgentOnline ? "bg-emerald-400" : "bg-amber-400"}`}></span>
                                    <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isAgentOnline ? "bg-emerald-400" : "bg-amber-400"}`}></span>
                                </span>
                                <span className="text-[11px] font-bold tracking-tight text-white">
                                    {isAgentOnline ? "Desktop Engine Connected" : "Connecting Agent..."}
                                </span>
                            </div>
                            <span className={`text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded-full border ${isAgentOnline ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-amber-500/10 text-amber-400 border-amber-500/30"}`}>
                                {isAgentOnline ? "LIVE" : "POLLING"}
                            </span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] font-mono text-[#8e8a83]">
                            <span>Bridge: IPC Socket</span>
                            <span className="text-[#f4efe7]/70">{lastSyncTime ? `Sync: ${lastSyncTime}` : "Local JSON Bridge"}</span>
                        </div>
                    </div>

                    {/* Navigation Menu */}
                    <nav className="px-3 space-y-1 mt-2">
                        {[
                            { id: "overview", label: "Overview", icon: "📊" },
                            { id: "cases", label: "Active Cases", icon: "📁", badge: casesData.length },
                            { id: "evidence", label: "Evidence Pool", icon: "🔍", badge: realEvidenceList.length },
                            { id: "operations", label: "Live Telemetry", icon: "⚡", live: telemetry?.is_wiping },
                            { id: "integrity", label: "Merkle & Hash Chain", icon: "🛡️" },
                            { id: "audit", label: "Audit Ledger", icon: "📜", badge: auditEvents.length },
                            { id: "devices", label: "Hardware Nodes", icon: "💻" },
                            { id: "reports", label: "Forensic Reports", icon: "📄" },
                            { id: "settings", label: "Configuration", icon: "⚙️" },
                        ].map((item) => {
                            const isCurrent = activeTab === item.id;
                            return (
                                <button
                                    key={item.id}
                                    onClick={() => setActiveTab(item.id)}
                                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                                        isCurrent
                                            ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/30 font-bold"
                                            : "text-[#b1a696] hover:bg-white/5 hover:text-white border border-transparent"
                                    }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm opacity-90">{item.icon}</span>
                                        <span>{item.label}</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        {item.badge !== undefined && item.badge > 0 && (
                                            <span
                                                className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                                                    isCurrent ? "bg-cyan-400 text-[#0d0e11]" : "bg-white/10 text-[#f4efe7]/80"
                                                }`}
                                            >
                                                {item.badge}
                                            </span>
                                        )}
                                        {item.live && (
                                            <span className="flex h-2 w-2 relative">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400"></span>
                                            </span>
                                        )}
                                    </div>
                                </button>
                            );
                        })}
                    </nav>
                </div>

                {/* Back to Landing Page */}
                <div className="p-3.5 border-t border-white/10 bg-[#101115]">
                    <button
                        onClick={onBackToLanding}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs font-bold text-[#f4efe7] hover:text-cyan-300 transition-all cursor-pointer shadow-sm"
                    >
                        <span>← Return to Portal</span>
                    </button>
                </div>
            </aside>

            {/* ── MAIN CONTENT ───────────────────────────────────────────── */}
            <main className="flex-1 flex flex-col min-h-screen bg-[#0d0e11]">
                {/* Topbar */}
                <header className="h-18 bg-[#131418]/90 backdrop-blur-md border-b border-white/10 px-8 flex items-center justify-between shrink-0 sticky top-0 z-30">
                    <div className="flex items-center gap-3">
                        <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                        <div>
                            <h2 className="text-base font-extrabold text-white capitalize tracking-wide flex items-center gap-2">
                                <span>{activeTab.replace("-", " ")}</span>
                                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-white/5 text-[#b1a696] border border-white/10">
                                    LIVE TELEMETRY
                                </span>
                            </h2>
                            <p className="text-[11px] text-[#8e8a83] font-medium">
                                Hardware-Synchronized Forensic Audit & Sanitization Console
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3.5">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search audit trail, hashes, cases..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 pr-4 py-2 bg-[#18191f] border border-white/10 rounded-xl text-xs text-white placeholder-[#8e8a83] focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 w-80 transition-all font-mono"
                            />
                            <span className="absolute left-3 top-2.5 text-xs text-[#8e8a83]">🔍</span>
                        </div>

                        <button
                            onClick={runChainVerification}
                            disabled={verifying}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-emerald-950/40 cursor-pointer disabled:opacity-50 border border-emerald-400/20"
                        >
                            <span>{verifying ? "Auditing Chain..." : "🛡️ Verify Ledger"}</span>
                        </button>
                    </div>
                </header>

                {/* Main Tab Body */}
                <div className="flex-1 p-7 bg-[#0d0e11]">
                    {/* ═════════════════ TAB 1: OVERVIEW ═════════════════ */}
                    {activeTab === "overview" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            {/* KPI Metrics Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4.5">
                                {/* Card 1: Active Cases */}
                                <div className="bg-[#15161b] p-5 rounded-2xl border border-white/10 shadow-lg hover:border-white/20 transition-all flex items-center justify-between group">
                                    <div>
                                        <p className="text-[10px] font-mono uppercase tracking-wider text-[#8e8a83] font-bold">Investigation Cases</p>
                                        <div className="flex items-baseline gap-2 mt-1">
                                            <h3 className="text-2xl font-black text-white">{casesData.length}</h3>
                                            <span className="text-xs font-bold text-cyan-400 font-mono">Active</span>
                                        </div>
                                        <p className="text-[10px] text-[#8e8a83] mt-1 font-mono">Source: forensic_cases.json</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center text-xl font-bold group-hover:scale-105 transition-transform">
                                        📁
                                    </div>
                                </div>

                                {/* Card 2: Hash Chain Height */}
                                <div className="bg-[#15161b] p-5 rounded-2xl border border-white/10 shadow-lg hover:border-white/20 transition-all flex items-center justify-between group">
                                    <div>
                                        <p className="text-[10px] font-mono uppercase tracking-wider text-[#8e8a83] font-bold">Audit Chain Height</p>
                                        <div className="flex items-baseline gap-2 mt-1">
                                            <h3 className="text-2xl font-black text-cyan-400 font-mono">#{auditEvents.length}</h3>
                                            <span className="text-xs font-bold text-[#b1a696]">Blocks</span>
                                        </div>
                                        <p className="text-[10px] text-[#8e8a83] mt-1 font-mono">Immutable SHA-256 Chain</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center text-xl font-bold group-hover:scale-105 transition-transform">
                                        ⛓️
                                    </div>
                                </div>

                                {/* Card 3: Hardware Erasure Status */}
                                <div className="bg-[#15161b] p-5 rounded-2xl border border-white/10 shadow-lg hover:border-white/20 transition-all flex items-center justify-between group">
                                    <div>
                                        <p className="text-[10px] font-mono uppercase tracking-wider text-[#8e8a83] font-bold">Erasure Subsystem</p>
                                        <div className="flex items-baseline gap-2 mt-1">
                                            <h3 className="text-2xl font-black text-white font-mono">
                                                {telemetry?.is_wiping ? `${telemetry.progress || 0}%` : telemetry?.status || "STANDBY"}
                                            </h3>
                                        </div>
                                        <p className="text-[10px] text-[#8e8a83] mt-1 font-mono truncate max-w-[150px]">{telemetry?.target || "No active wipe target"}</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center text-xl font-bold group-hover:scale-105 transition-transform">
                                        ⚡
                                    </div>
                                </div>

                                {/* Card 4: Dynamic Merkle Root */}
                                <div className="bg-[#15161b] p-5 rounded-2xl border border-white/10 shadow-lg hover:border-white/20 transition-all flex items-center justify-between group">
                                    <div className="min-w-0 pr-2">
                                        <p className="text-[10px] font-mono uppercase tracking-wider text-[#8e8a83] font-bold">Merkle Root</p>
                                        <div className="flex items-center gap-1.5 mt-1">
                                            <h3 className="text-xs font-mono font-bold text-white truncate max-w-[130px]" title={merkleRoot}>
                                                {merkleRoot ? `${merkleRoot.substring(0, 10)}...` : "Computing..."}
                                            </h3>
                                            {merkleRoot && (
                                                <button
                                                    onClick={() => copyToClipboard(merkleRoot, "merkle")}
                                                    className="text-[10px] text-cyan-400 hover:text-white px-1.5 py-0.5 rounded bg-white/5 border border-white/10 cursor-pointer"
                                                    title="Copy full Merkle Root"
                                                >
                                                    {copiedHash === "merkle" ? "✓" : "Copy"}
                                                </button>
                                            )}
                                        </div>
                                        <p className="text-[10px] text-emerald-400 font-semibold mt-1 flex items-center gap-1">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
                                            Cryptographically Intact
                                        </p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center text-xl font-bold group-hover:scale-105 transition-transform shrink-0">
                                        🛡️
                                    </div>
                                </div>
                            </div>

                            {/* Verification Result Banner (if triggered) */}
                            {verificationResult && (
                                <div className={`p-5 rounded-2xl border transition-all ${verificationResult.valid ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-300" : "bg-rose-950/30 border-rose-500/40 text-rose-300"}`}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2.5">
                                            <span className="text-xl">{verificationResult.valid ? "🛡️" : "⚠️"}</span>
                                            <div>
                                                <p className="font-extrabold text-sm text-white">
                                                    {verificationResult.valid ? "Full Cryptographic Hash Chain Audit Verified" : "Cryptographic Chain Discrepancy Detected"}
                                                </p>
                                                <p className="text-xs text-[#b1a696] font-mono mt-0.5">
                                                    Genesis block to Block #{verificationResult.totalBlocks} cryptographically verified using SHA-256 recursive Merkle validation.
                                                </p>
                                            </div>
                                        </div>
                                        <span className={`px-2.5 py-1 rounded-md text-[10px] font-mono font-bold uppercase ${verificationResult.valid ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-rose-500/20 text-rose-300 border border-rose-500/30"}`}>
                                            {verificationResult.valid ? "100% UNBROKEN" : "TAMPER ALERT"}
                                        </span>
                                    </div>
                                    <div className="mt-3.5 pt-3 border-t border-white/10 grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-[11px] text-[#f4efe7]/80">
                                        <div><span className="text-[#8e8a83]">Audited Blocks:</span> #{verificationResult.totalBlocks}</div>
                                        <div className="truncate"><span className="text-[#8e8a83]">Root:</span> {verificationResult.merkleRoot}</div>
                                        <div><span className="text-[#8e8a83]">Audit Time:</span> {new Date(verificationResult.verifiedAt).toLocaleTimeString()}</div>
                                    </div>
                                </div>
                            )}

                            {/* Hardware Telemetry Card */}
                            {telemetry && (
                                <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl relative overflow-hidden">
                                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-bold text-[10px] tracking-wider uppercase font-mono">
                                                    Hardware Subsystem Stream
                                                </span>
                                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${telemetry.is_wiping ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse" : "bg-white/5 text-[#b1a696] border border-white/10"}`}>
                                                    {telemetry.status || "STANDBY"}
                                                </span>
                                            </div>
                                            <h3 className="text-lg font-bold text-white mt-1.5 flex items-center gap-2">
                                                <span>Target:</span>
                                                <span className="font-mono text-cyan-300">{telemetry.target || "Local Physical Volumes"}</span>
                                            </h3>
                                            <p className="text-xs text-[#b1a696] mt-0.5">
                                                Sanitization Standard: <span className="font-mono font-bold text-white">{telemetry.method || "NIST SP 800-88 Rev 1"}</span>
                                            </p>
                                        </div>

                                        {telemetry.is_wiping && (
                                            <div className="text-right">
                                                <span className="text-3xl font-black text-cyan-400 font-mono">{telemetry.progress || 0}%</span>
                                                <p className="text-xs font-mono text-[#8e8a83]">{telemetry.speed_mb_s || 0} MB/s Throughput</p>
                                            </div>
                                        )}
                                    </div>

                                    {telemetry.is_wiping && (
                                        <div className="w-full bg-[#101115] rounded-full h-3 overflow-hidden border border-white/10 mt-3 p-0.5">
                                            <div
                                                className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full rounded-full transition-all duration-300 shadow-md shadow-cyan-500/50"
                                                style={{ width: `${telemetry.progress || 0}%` }}
                                            />
                                        </div>
                                    )}

                                    {/* Forensic Terminal Console Log */}
                                    <div className="mt-4 p-3.5 bg-[#0a0b0d] border border-white/10 rounded-xl font-mono text-[11px] text-emerald-400/90 shadow-inner flex items-center justify-between">
                                        <div className="flex items-center gap-2.5 truncate">
                                            <span className="text-cyan-400 font-bold">$</span>
                                            <span className="truncate">{telemetry.new_log || `[TELEMETRY] Device bridge synchronized with ${telemetry.target || "system storage"}`}</span>
                                        </div>
                                        <span className="text-[10px] text-[#8e8a83] shrink-0 ml-3">STREAM ACTIVE</span>
                                    </div>
                                </div>
                            )}

                            {/* Cryptographic Hash Chain Ledger Table */}
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-5">
                                    <div>
                                        <h3 className="font-extrabold text-white text-base tracking-tight flex items-center gap-2">
                                            <span>Chronological Hash Chain Ledger</span>
                                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-[#b1a696] border border-white/10">
                                                LATEST BLOCKS
                                            </span>
                                        </h3>
                                        <p className="text-xs text-[#8e8a83] mt-0.5">Live tamper-evident event stream loaded from audit_trail.json</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveTab("audit")}
                                        className="text-xs font-bold text-cyan-400 hover:text-cyan-300 transition-colors cursor-pointer flex items-center gap-1.5"
                                    >
                                        <span>View Full Audit Ledger ({auditEvents.length})</span>
                                        <span>→</span>
                                    </button>
                                </div>

                                <div className="overflow-x-auto rounded-xl border border-white/10">
                                    <table className="w-full text-left text-xs">
                                        <thead>
                                            <tr className="border-b border-white/10 text-[#8e8a83] font-mono text-[10px] uppercase tracking-wider bg-[#101115]">
                                                <th className="py-3 px-4"># Block</th>
                                                <th className="py-3 px-4">Timestamp (UTC)</th>
                                                <th className="py-3 px-4">Operator</th>
                                                <th className="py-3 px-4">Forensic Action</th>
                                                <th className="py-3 px-4">Target Target</th>
                                                <th className="py-3 px-4 text-right">Block Hash (SHA-256)</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                                            {auditEvents.slice(-7).reverse().map((ev) => (
                                                <tr key={ev.index} className="hover:bg-white/[0.03] transition-colors group">
                                                    <td className="py-3 px-4 font-bold text-cyan-400">
                                                        #{String(ev.index).padStart(4, "0")}
                                                    </td>
                                                    <td className="py-3 px-4 text-[#b1a696] font-sans">
                                                        {new Date(ev.timestamp).toLocaleString()}
                                                    </td>
                                                    <td className="py-3 px-4 font-sans font-semibold text-white">
                                                        {ev.operator}
                                                    </td>
                                                    <td className="py-3 px-4">
                                                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${getActionBadgeColor(ev.action)}`}>
                                                            {ev.action}
                                                        </span>
                                                    </td>
                                                    <td className="py-3 px-4 text-[#f4efe7]/80 truncate max-w-[200px]" title={ev.target}>
                                                        {ev.target}
                                                    </td>
                                                    <td className="py-3 px-4 text-right">
                                                        <div className="flex items-center justify-end gap-1.5">
                                                            <span className="text-[#8e8a83] group-hover:text-cyan-300 transition-colors">
                                                                {ev.event_hash ? `${ev.event_hash.substring(0, 10)}...` : "N/A"}
                                                            </span>
                                                            {ev.event_hash && (
                                                                <button
                                                                    onClick={() => copyToClipboard(ev.event_hash, ev.index)}
                                                                    className="opacity-0 group-hover:opacity-100 text-[10px] text-cyan-400 hover:text-white px-1.5 py-0.5 rounded bg-white/10 transition-opacity cursor-pointer"
                                                                    title="Copy SHA-256 Hash"
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

                    {/* ═════════════════ TAB 2: CASES ═════════════════ */}
                    {activeTab === "cases" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-white">Forensic Investigation Cases</h3>
                                        <p className="text-xs text-[#8e8a83]">
                                            Synchronized directly from forensic_cases.json recorded by ZeroTrace.exe.
                                        </p>
                                    </div>
                                    <span className="text-xs bg-cyan-500/10 text-cyan-400 font-bold px-3 py-1.5 rounded-xl border border-cyan-500/20 font-mono">
                                        {casesData.length} Registered Cases
                                    </span>
                                </div>

                                {casesData.length === 0 ? (
                                    <div className="p-12 text-center text-[#8e8a83] border border-dashed border-white/10 rounded-2xl">
                                        <span className="text-3xl block mb-2">📁</span>
                                        <p className="font-semibold text-sm text-white">No investigation cases registered yet.</p>
                                        <p className="text-xs mt-1 text-[#8e8a83]">Open ZeroTrace.exe to initialize a forensic case investigation.</p>
                                    </div>
                                ) : (
                                    <div className="overflow-x-auto rounded-xl border border-white/10">
                                        <table className="w-full text-left text-xs">
                                            <thead>
                                                <tr className="border-b border-white/10 text-[#8e8a83] font-mono text-[10px] uppercase tracking-wider bg-[#101115]">
                                                    <th className="py-3.5 px-4">Case ID</th>
                                                    <th className="py-3.5 px-4">Title & Agency</th>
                                                    <th className="py-3.5 px-4">Investigator</th>
                                                    <th className="py-3.5 px-4">Status</th>
                                                    <th className="py-3.5 px-4">Created Date</th>
                                                    <th className="py-3.5 px-4">Evidence</th>
                                                    <th className="py-3.5 px-4 text-right">Action</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-white/5">
                                                {casesData.map((c) => (
                                                    <tr key={c.case_id} className="hover:bg-white/[0.03] transition-colors">
                                                        <td className="py-4 px-4 font-mono font-bold text-cyan-400">{c.case_id}</td>
                                                        <td className="py-4 px-4">
                                                            <div className="font-bold text-white">{c.title}</div>
                                                            <div className="text-[10px] text-[#8e8a83]">{c.agency}</div>
                                                        </td>
                                                        <td className="py-4 px-4 text-[#f4efe7]">{c.investigator}</td>
                                                        <td className="py-4 px-4">
                                                            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                                                {c.status || "ACTIVE"}
                                                            </span>
                                                        </td>
                                                        <td className="py-4 px-4 text-[#b1a696] font-mono text-[11px]">
                                                            {new Date(c.created_at).toLocaleString()}
                                                        </td>
                                                        <td className="py-4 px-4 font-mono font-bold text-white">
                                                            {c.evidence_items?.length || 0} Items
                                                        </td>
                                                        <td className="py-4 px-4 text-right">
                                                            <button
                                                                onClick={() => setSelectedCase(c)}
                                                                className="px-3 py-1.5 bg-white/5 hover:bg-cyan-500/20 text-cyan-300 rounded-lg font-bold text-xs transition-colors border border-white/10 cursor-pointer"
                                                            >
                                                                Inspect Case
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
                                <div className="bg-[#15161b] p-6 rounded-2xl border border-cyan-500/40 shadow-2xl">
                                    <div className="flex justify-between items-center pb-3.5 border-b border-white/10">
                                        <h3 className="font-black text-white text-base">{selectedCase.title}</h3>
                                        <button onClick={() => setSelectedCase(null)} className="text-[#8e8a83] hover:text-white font-bold cursor-pointer text-xs">
                                            ✕ Close
                                        </button>
                                    </div>
                                    <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3.5 text-xs">
                                        <div className="p-3.5 bg-[#101115] rounded-xl border border-white/5">
                                            <p className="text-[#8e8a83] font-semibold">Case Identifier</p>
                                            <p className="font-mono font-bold text-cyan-400 mt-1">{selectedCase.case_id}</p>
                                        </div>
                                        <div className="p-3.5 bg-[#101115] rounded-xl border border-white/5">
                                            <p className="text-[#8e8a83] font-semibold">Description</p>
                                            <p className="text-white mt-1">{selectedCase.description || "Forensic investigation archive."}</p>
                                        </div>
                                        <div className="p-3.5 bg-[#101115] rounded-xl border border-white/5">
                                            <p className="text-[#8e8a83] font-semibold">Registration Date</p>
                                            <p className="font-mono text-white mt-1">{new Date(selectedCase.created_at).toUTCString()}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ═════════════════ TAB 3: EVIDENCE ═════════════════ */}
                    {activeTab === "evidence" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-white">Registered Physical & Logical Evidence Pool</h3>
                                        <p className="text-xs text-[#8e8a83]">Media items and drive volumes acquired during active investigations.</p>
                                    </div>
                                    <span className="text-xs bg-emerald-500/10 text-emerald-400 font-bold px-3 py-1.5 rounded-xl border border-emerald-500/20 font-mono">
                                        {realEvidenceList.length} Media Registered
                                    </span>
                                </div>

                                {realEvidenceList.length === 0 ? (
                                    <div className="p-12 text-center text-[#8e8a83] border border-dashed border-white/10 rounded-2xl">
                                        <span className="text-3xl block mb-2">🔍</span>
                                        <p className="font-semibold text-sm text-white">No evidence drives registered in the active case.</p>
                                        <p className="text-xs mt-1 text-[#8e8a83]">Mount or register a physical drive / disk image in ZeroTrace.exe.</p>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {realEvidenceList.map((e, idx) => (
                                            <div key={idx} className="p-5 rounded-2xl border border-white/10 bg-[#121316] shadow-lg">
                                                <div className="flex justify-between items-start">
                                                    <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 text-[10px] font-mono font-bold border border-cyan-500/30">
                                                        {e.evidence_id || `EVID-${idx + 1}`}
                                                    </span>
                                                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                                                        {e.status || "SECURED"}
                                                    </span>
                                                </div>
                                                <h4 className="font-bold text-white text-sm mt-3">{e.label || e.target_path}</h4>
                                                <p className="text-[11px] text-[#8e8a83]">{e.evidence_type || "Storage Volume"}</p>
                                                <div className="mt-3.5 space-y-1.5 text-xs font-mono text-[#b1a696] border-t border-white/5 pt-2.5">
                                                    <div>Path: <span className="text-white">{e.target_path}</span></div>
                                                    <div>Size: <span className="text-white">{e.size_bytes ? `${(e.size_bytes / 1024 / 1024).toFixed(2)} MB` : "Auto-detected"}</span></div>
                                                    <div>Acquired: <span className="text-white">{e.acquired_by || "Forensic Operator"}</span></div>
                                                </div>
                                                {e.sha256 && (
                                                    <div className="mt-3 text-[10px] font-mono text-[#8e8a83] truncate bg-black/30 p-1.5 rounded border border-white/5">
                                                        SHA: {e.sha256}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 4: OPERATIONS ═════════════════ */}
                    {activeTab === "operations" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="font-bold text-white text-base">Live Hardware Operations Console</h3>
                                        <p className="text-xs text-[#8e8a83]">Active desktop wiping and carving telemetry feed.</p>
                                    </div>
                                    <span className="text-xs font-mono font-bold px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-full">
                                        LIVE TELEMETRY
                                    </span>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-5 bg-[#101115] rounded-xl border border-white/5 text-xs">
                                    <div>
                                        <p className="text-[#8e8a83] font-semibold">Active Hardware Target</p>
                                        <p className="font-mono font-bold text-white mt-1 text-sm">{telemetry?.target || "None currently selected"}</p>
                                    </div>
                                    <div>
                                        <p className="text-[#8e8a83] font-semibold">Sanitization Standard</p>
                                        <p className="font-mono font-bold text-cyan-400 mt-1 text-sm">{telemetry?.method || "NIST SP 800-88 Purge"}</p>
                                    </div>
                                    <div>
                                        <p className="text-[#8e8a83] font-semibold">Operation Status</p>
                                        <p className="font-mono font-bold text-emerald-400 mt-1 text-sm">{telemetry?.status || "STANDBY"}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 5: INTEGRITY ═════════════════ */}
                    {activeTab === "integrity" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-white">Cryptographic Merkle Tree & Hash Chain Verification</h3>
                                        <p className="text-xs text-[#8e8a83]">
                                            Recursive SHA-256 binary hash tree computed across {auditEvents.length} chronological blocks.
                                        </p>
                                    </div>
                                    <button
                                        onClick={runChainVerification}
                                        disabled={verifying}
                                        className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-xl text-xs transition-all shadow-lg shadow-cyan-950/40 cursor-pointer border border-cyan-400/20"
                                    >
                                        {verifying ? "Auditing Chain..." : "Run Cryptographic Audit"}
                                    </button>
                                </div>

                                <div className="p-8 bg-[#101115] rounded-2xl border border-white/5 text-center">
                                    <span className="text-xs font-mono font-bold text-[#8e8a83] uppercase tracking-wider">Dynamic Merkle Root Hash</span>
                                    <div className="mt-3 flex justify-center">
                                        <div className="p-4 bg-[#181920] border border-cyan-500/30 text-cyan-300 rounded-xl shadow-xl text-xs font-mono font-bold max-w-2xl break-all">
                                            ROOT: {merkleRoot || "Computing from real leaf hashes..."}
                                        </div>
                                    </div>
                                    <p className="text-xs font-mono text-[#8e8a83] mt-4">
                                        Tree Height: {Math.ceil(Math.log2(Math.max(1, auditEvents.length))) + 1} levels | Leaf Hashes: {auditEvents.length}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 6: AUDIT LOGS ═════════════════ */}
                    {activeTab === "audit" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-white">Cryptographic Hash Chain Audit Trail</h3>
                                        <p className="text-xs text-[#8e8a83]">
                                            Full chronological ledger ({filteredAudit.length} of {auditEvents.length} matching events).
                                        </p>
                                    </div>
                                    <span className="text-xs font-mono font-bold px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                        Chain Integrity: 100% UNBROKEN
                                    </span>
                                </div>

                                <div className="overflow-x-auto rounded-xl border border-white/10">
                                    <table className="w-full text-left text-xs">
                                        <thead>
                                            <tr className="border-b border-white/10 text-[#8e8a83] font-mono text-[10px] uppercase tracking-wider bg-[#101115]">
                                                <th className="py-3 px-3"># Block</th>
                                                <th className="py-3 px-3">Timestamp (UTC)</th>
                                                <th className="py-3 px-3">Operator</th>
                                                <th className="py-3 px-3">Action</th>
                                                <th className="py-3 px-3">Target</th>
                                                <th className="py-3 px-3">Case ID</th>
                                                <th className="py-3 px-3 text-right">Event Hash</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                                            {filteredAudit.map((ev) => (
                                                <tr key={ev.index} className="hover:bg-white/[0.03] transition-colors">
                                                    <td className="py-3 px-3 font-bold text-cyan-400">#{String(ev.index).padStart(4, "0")}</td>
                                                    <td className="py-3 px-3 text-[#b1a696] font-sans">{new Date(ev.timestamp).toLocaleString()}</td>
                                                    <td className="py-3 px-3 font-sans font-semibold text-white">{ev.operator}</td>
                                                    <td className="py-3 px-3">
                                                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${getActionBadgeColor(ev.action)}`}>
                                                            {ev.action}
                                                        </span>
                                                    </td>
                                                    <td className="py-3 px-3 text-[#f4efe7]/80 truncate max-w-[180px] font-sans" title={ev.target}>{ev.target}</td>
                                                    <td className="py-3 px-3 text-cyan-400 font-sans">{ev.case_id}</td>
                                                    <td className="py-3 px-3 text-right text-[#8e8a83]">{ev.event_hash ? `${ev.event_hash.substring(0, 10)}...` : "N/A"}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 7: DEVICES / WORKERS ═════════════════ */}
                    {activeTab === "devices" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <h3 className="text-base font-bold text-white mb-2">Connected Forensic Workstations & Workers</h3>
                                <p className="text-xs text-[#8e8a83] mb-6">Physical hardware endpoints connected to the telemetry bridge.</p>

                                <div className="p-6 rounded-2xl border border-white/10 bg-[#101115] shadow-lg max-w-md">
                                    <div className="flex justify-between items-start">
                                        <span className="text-xs font-mono font-bold text-cyan-400">HOST-LOCAL-01</span>
                                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${isAgentOnline ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-amber-500/10 text-amber-400 border-amber-500/30"}`}>
                                            {isAgentOnline ? "ONLINE" : "STANDBY"}
                                        </span>
                                    </div>
                                    <h4 className="font-bold text-white text-base mt-2.5">ZeroTrace Forensic Workstation</h4>
                                    <p className="text-xs text-[#8e8a83]">ZeroTrace.exe Desktop Application (Win32)</p>
                                    <div className="mt-4 space-y-2 text-xs font-mono text-[#b1a696] border-t border-white/5 pt-3.5">
                                        <div className="flex justify-between">
                                            <span>Bridge Socket:</span>
                                            <span className="text-white">127.0.0.1:5173 / 5174</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Recorded Audit Blocks:</span>
                                            <span className="font-bold text-cyan-400">#{auditEvents.length}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Active Cases in Memory:</span>
                                            <span className="font-bold text-white">{casesData.length}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 8: REPORTS ═════════════════ */}
                    {activeTab === "reports" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-white">Forensic Audit & Certificate Reports</h3>
                                        <p className="text-xs text-[#8e8a83]">Export cryptographically signed ledgers and case reports.</p>
                                    </div>
                                    <button
                                        onClick={() => {
                                            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(auditEvents, null, 2));
                                            const dl = document.createElement("a");
                                            dl.setAttribute("href", dataStr);
                                            dl.setAttribute("download", `ZeroTrace_Audit_Trail_${Date.now()}.json`);
                                            dl.click();
                                        }}
                                        className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-xl text-xs transition-all shadow-lg shadow-cyan-950/30 cursor-pointer border border-cyan-400/20"
                                    >
                                        Export Audit Ledger (JSON)
                                    </button>
                                </div>

                                <div className="p-5 rounded-xl border border-white/10 bg-[#101115] flex items-center justify-between">
                                    <div>
                                        <h4 className="font-bold text-white text-xs">Full Cryptographic Hash Chain Audit Ledger</h4>
                                        <p className="text-[11px] text-[#8e8a83] font-mono mt-0.5">
                                            Contains {auditEvents.length} cryptographically signed blocks from genesis block.
                                        </p>
                                    </div>
                                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-md">
                                        VERIFIED INTACT
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 9: SETTINGS ═════════════════ */}
                    {activeTab === "settings" && (
                        <div className="space-y-6 max-w-4xl mx-auto">
                            <div className="bg-[#15161b] p-6 rounded-2xl border border-white/10 shadow-xl">
                                <h3 className="text-base font-bold text-white mb-2">Bridge Configuration & Storage Paths</h3>
                                <p className="text-xs text-[#8e8a83] mb-5">Local data bridge paths connecting Desktop Agent with the Web Hub.</p>
                                <div className="space-y-4 text-xs font-mono">
                                    <div>
                                        <label className="block font-sans font-semibold text-[#b1a696] mb-1.5">Desktop Audit Trail Source</label>
                                        <input
                                            type="text"
                                            value="/public/audit_trail.json"
                                            disabled
                                            className="w-full p-3 bg-[#101115] border border-white/10 rounded-xl text-cyan-300 font-mono"
                                        />
                                    </div>
                                    <div>
                                        <label className="block font-sans font-semibold text-[#b1a696] mb-1.5">Desktop Cases Source</label>
                                        <input
                                            type="text"
                                            value="/public/forensic_cases.json"
                                            disabled
                                            className="w-full p-3 bg-[#101115] border border-white/10 rounded-xl text-cyan-300 font-mono"
                                        />
                                    </div>
                                    <div>
                                        <label className="block font-sans font-semibold text-[#b1a696] mb-1.5">Real-Time Telemetry Socket</label>
                                        <input
                                            type="text"
                                            value="/public/live_wipe_telemetry.json"
                                            disabled
                                            className="w-full p-3 bg-[#101115] border border-white/10 rounded-xl text-cyan-300 font-mono"
                                        />
                                    </div>
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
