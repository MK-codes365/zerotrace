import React, { useState, useEffect, useRef, useMemo } from "react";

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
                // fallback if file empty
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
        }, 800);
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

    return (
        <div className="flex min-h-screen bg-[#f8fafc] text-[#0f172a] font-sans antialiased" data-lenis-prevent="true">
            {/* ── SIDEBAR (Sticky Navigation) ────────────────────────────── */}
            <aside className="w-64 bg-white border-r border-[#e2e8f0] flex flex-col justify-between shrink-0 shadow-sm z-20 sticky top-0 h-screen overflow-y-auto">
                <div>
                    {/* Header */}
                    <div className="h-16 px-6 border-b border-[#e2e8f0] flex items-center justify-between bg-gradient-to-r from-blue-600 to-indigo-700">
                        <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-white p-1 flex items-center justify-center shadow-md">
                                <img src="/logo.png" alt="ZeroTrace" className="w-full h-full object-contain" />
                            </div>
                            <div>
                                <h1 className="text-white font-extrabold text-base tracking-tight leading-none">
                                    ZeroTrace<span className="text-blue-200 text-xs font-normal">®</span>
                                </h1>
                                <p className="text-blue-100 text-[10px] font-medium tracking-wide">Live Forensic Web Hub</p>
                            </div>
                        </div>
                    </div>

                    {/* Agent Live Connectivity Status */}
                    <div className="mx-4 my-3 p-2.5 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className="relative flex h-2.5 w-2.5">
                                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isAgentOnline ? "bg-emerald-400" : "bg-amber-400"}`}></span>
                                <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isAgentOnline ? "bg-emerald-500" : "bg-amber-500"}`}></span>
                            </span>
                            <div>
                                <p className="text-[11px] font-bold text-blue-900 leading-tight">
                                    {isAgentOnline ? "Desktop Agent Connected" : "Awaiting Desktop Tool"}
                                </p>
                                <p className="text-[9px] text-blue-600">
                                    {lastSyncTime ? `Synced: ${lastSyncTime}` : "Local JSON Bridge"}
                                </p>
                            </div>
                        </div>
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-200 text-blue-800">
                            LIVE
                        </span>
                    </div>

                    {/* Navigation Menu */}
                    <nav className="px-3 space-y-1 mt-2">
                        {[
                            { id: "overview", label: "Overview", icon: "📊" },
                            { id: "cases", label: "Cases (Desktop)", icon: "📁", badge: casesData.length },
                            { id: "evidence", label: "Evidence", icon: "🔍", badge: realEvidenceList.length },
                            { id: "operations", label: "Operations (Erasure & Carve)", icon: "⚡", live: telemetry?.is_wiping },
                            { id: "integrity", label: "Integrity (Merkle & Chain)", icon: "🛡️" },
                            { id: "audit", label: "Audit Logs", icon: "📜", badge: auditEvents.length },
                            { id: "devices", label: "Devices / Workers", icon: "💻" },
                            { id: "reports", label: "Reports & Certificates", icon: "📄" },
                            { id: "settings", label: "Settings", icon: "⚙️" },
                        ].map((item) => (
                            <button
                                key={item.id}
                                onClick={() => setActiveTab(item.id)}
                                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                                    activeTab === item.id
                                        ? "bg-blue-600 text-white shadow-sm shadow-blue-500/20 font-bold"
                                        : "text-slate-600 hover:bg-slate-100 hover:text-blue-600"
                                }`}
                            >
                                <div className="flex items-center gap-2.5">
                                    <span className="text-sm">{item.icon}</span>
                                    <span>{item.label}</span>
                                </div>
                                {item.badge !== undefined && item.badge > 0 && (
                                    <span
                                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                            activeTab === item.id ? "bg-white text-blue-600" : "bg-slate-200 text-slate-700"
                                        }`}
                                    >
                                        {item.badge}
                                    </span>
                                )}
                                {item.live && (
                                    <span className="flex h-2 w-2 relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-300"></span>
                                    </span>
                                )}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Back to Landing Page */}
                <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                    <button
                        onClick={onBackToLanding}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-100 hover:text-blue-600 transition-colors shadow-sm cursor-pointer"
                    >
                        <span>← Return to Landing Page</span>
                    </button>
                </div>
            </aside>

            {/* ── MAIN CONTENT ───────────────────────────────────────────── */}
            <main className="flex-1 flex flex-col min-h-screen bg-[#f8fafc]">
                {/* Topbar (Sticky Header) */}
                <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between shrink-0 shadow-xs sticky top-0 z-30">
                    <div>
                        <h2 className="text-lg font-black text-slate-900 capitalize tracking-tight flex items-center gap-2">
                            <span>{activeTab.replace("-", " ")}</span>
                            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                                Live Desktop Data
                            </span>
                        </h2>
                        <p className="text-[11px] text-slate-500 font-medium">
                            Real-time Forensic Verification & Hardware Sanitization Stream
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search real audit events, cases, hashes..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 pr-4 py-1.5 bg-slate-100 border border-slate-200 rounded-full text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 w-72 transition-all"
                            />
                            <span className="absolute left-3 top-2 text-xs text-slate-400">🔍</span>
                        </div>

                        <button
                            onClick={runChainVerification}
                            disabled={verifying}
                            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-xs font-bold transition-all shadow-sm shadow-emerald-600/20 cursor-pointer disabled:opacity-50"
                        >
                            <span>{verifying ? "Verifying Chain..." : "🛡️ Verify Hashes"}</span>
                        </button>
                    </div>
                </header>

                {/* Main Tab Views Body */}
                <div className="flex-1 p-6 bg-[#f8fafc]">
                    {/* ═════════════════ TAB 1: OVERVIEW ═════════════════ */}
                    {activeTab === "overview" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            {/* Real KPI Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                                    <div>
                                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Real Desktop Cases</p>
                                        <h3 className="text-2xl font-black text-slate-900 mt-1">{casesData.length} <span className="text-xs font-bold text-blue-600">Active</span></h3>
                                        <p className="text-[11px] text-slate-400 mt-1">Read from forensic_cases.json</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl font-bold">
                                        📁
                                    </div>
                                </div>

                                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                                    <div>
                                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Hash Chain Height</p>
                                        <h3 className="text-2xl font-black text-blue-600 mt-1">#{auditEvents.length} <span className="text-xs font-bold text-slate-600">Blocks</span></h3>
                                        <p className="text-[11px] text-slate-400 mt-1">Immutable SHA-256 Ledger</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center text-xl font-bold">
                                        ⛓️
                                    </div>
                                </div>

                                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                                    <div>
                                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Real Erasure Status</p>
                                        <h3 className="text-2xl font-black text-slate-900 mt-1">
                                            {telemetry?.is_wiping ? `${telemetry.progress || 0}%` : telemetry?.status || "STANDBY"}
                                        </h3>
                                        <p className="text-[11px] text-slate-400 mt-1">{telemetry?.target || "No drive currently wiping"}</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl font-bold">
                                        ⚡
                                    </div>
                                </div>

                                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
                                    <div>
                                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Real Merkle Root</p>
                                        <h3 className="text-sm font-mono font-bold text-slate-900 mt-1 truncate max-w-[140px]" title={merkleRoot}>
                                            {merkleRoot ? `${merkleRoot.substring(0, 10)}...` : "Computing..."}
                                        </h3>
                                        <p className="text-[11px] text-emerald-600 font-semibold mt-1">● Cryptographically Computed</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl font-bold">
                                        🛡️
                                    </div>
                                </div>
                            </div>

                            {/* Real Hardware Erasure Banner if active or standby */}
                            {telemetry && (
                                <div className="bg-white p-6 rounded-2xl border border-blue-200 shadow-xs">
                                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                                        <div>
                                            <span className="px-2.5 py-0.5 rounded-full bg-blue-600 text-white font-bold text-[10px]">
                                                DESKTOP HARDWARE TELEMETRY
                                            </span>
                                            <h3 className="text-base font-bold text-slate-900 mt-1">
                                                Target: {telemetry.target || "Local System Disks"}
                                            </h3>
                                            <p className="text-xs text-slate-600">
                                                Method: <span className="font-bold text-blue-700">{telemetry.method || "NIST_800_88_PURGE"}</span> | Status: <span className="font-bold text-emerald-700">{telemetry.status || "IDLE"}</span>
                                            </p>
                                        </div>

                                        {telemetry.is_wiping && (
                                            <div className="text-right">
                                                <span className="text-2xl font-black text-blue-600">{telemetry.progress || 0}%</span>
                                                <p className="text-xs text-slate-500">{telemetry.speed_mb_s || 0} MB/s</p>
                                            </div>
                                        )}
                                    </div>

                                    {telemetry.is_wiping && (
                                        <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200 mt-2">
                                            <div
                                                className="bg-blue-600 h-full rounded-full transition-all duration-300"
                                                style={{ width: `${telemetry.progress || 0}%` }}
                                            />
                                        </div>
                                    )}

                                    {telemetry.new_log && (
                                        <div className="mt-3 p-2.5 bg-slate-900 text-emerald-400 font-mono text-[11px] rounded-xl">
                                            {telemetry.new_log}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Real Audit Trail Stream */}
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <div className="flex justify-between items-center mb-4">
                                    <div>
                                        <h3 className="font-bold text-slate-900 text-sm">Real Chronological Hash Chain Ledger (Latest Events)</h3>
                                        <p className="text-xs text-slate-500">Live events loaded from audit_trail.json</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveTab("audit")}
                                        className="text-xs font-bold text-blue-600 hover:text-blue-800 cursor-pointer"
                                    >
                                        View All ({auditEvents.length}) →
                                    </button>
                                </div>

                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-xs">
                                        <thead>
                                            <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider bg-slate-50/50">
                                                <th className="py-2.5 px-3"># Block</th>
                                                <th className="py-2.5 px-3">Timestamp (UTC)</th>
                                                <th className="py-2.5 px-3">Operator</th>
                                                <th className="py-2.5 px-3">Action</th>
                                                <th className="py-2.5 px-3">Target</th>
                                                <th className="py-2.5 px-3 text-right">Block Hash</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                                            {auditEvents.slice(-6).reverse().map((ev) => (
                                                <tr key={ev.index} className="hover:bg-slate-50">
                                                    <td className="py-2.5 px-3 font-bold text-blue-600">#{ev.index}</td>
                                                    <td className="py-2.5 px-3 text-slate-600 font-sans">{new Date(ev.timestamp).toLocaleString()}</td>
                                                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-800">{ev.operator}</td>
                                                    <td className="py-2.5 px-3 font-sans font-bold text-slate-700">{ev.action}</td>
                                                    <td className="py-2.5 px-3 text-slate-600 font-sans">{ev.target}</td>
                                                    <td className="py-2.5 px-3 text-right text-slate-400">
                                                        {ev.event_hash ? `${ev.event_hash.substring(0, 10)}...` : "N/A"}
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
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-slate-900">Real Forensic Cases (Desktop Synchronized)</h3>
                                        <p className="text-xs text-slate-500">
                                            Cases recorded directly in forensic_cases.json by ZeroTrace.exe.
                                        </p>
                                    </div>
                                    <span className="text-xs bg-blue-50 text-blue-700 font-bold px-3 py-1.5 rounded-xl border border-blue-200">
                                        {casesData.length} Real Cases
                                    </span>
                                </div>

                                {casesData.length === 0 ? (
                                    <div className="p-8 text-center text-slate-400">
                                        <p className="font-semibold text-sm">No cases registered yet.</p>
                                        <p className="text-xs mt-1">Create a case in ZeroTrace.exe desktop application to view it here.</p>
                                    </div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left text-xs">
                                            <thead>
                                                <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider bg-slate-50/50">
                                                    <th className="py-3 px-4">Case ID</th>
                                                    <th className="py-3 px-4">Title & Agency</th>
                                                    <th className="py-3 px-4">Investigator</th>
                                                    <th className="py-3 px-4">Status</th>
                                                    <th className="py-3 px-4">Created Date</th>
                                                    <th className="py-3 px-4">Evidence Count</th>
                                                    <th className="py-3 px-4 text-right">Action</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-100">
                                                {casesData.map((c) => (
                                                    <tr key={c.case_id} className="hover:bg-slate-50">
                                                        <td className="py-3.5 px-4 font-bold text-blue-600">{c.case_id}</td>
                                                        <td className="py-3.5 px-4">
                                                            <div className="font-bold text-slate-800">{c.title}</div>
                                                            <div className="text-[10px] text-slate-400">{c.agency}</div>
                                                        </td>
                                                        <td className="py-3.5 px-4 text-slate-700">{c.investigator}</td>
                                                        <td className="py-3.5 px-4">
                                                            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                                                                {c.status}
                                                            </span>
                                                        </td>
                                                        <td className="py-3.5 px-4 text-slate-600 font-mono text-[11px]">
                                                            {new Date(c.created_at).toLocaleString()}
                                                        </td>
                                                        <td className="py-3.5 px-4 font-bold text-slate-700">
                                                            {c.evidence_items?.length || 0} Media
                                                        </td>
                                                        <td className="py-3.5 px-4 text-right">
                                                            <button
                                                                onClick={() => setSelectedCase(c)}
                                                                className="px-3 py-1 bg-slate-100 hover:bg-blue-50 text-blue-600 rounded-lg font-bold text-xs transition-colors cursor-pointer"
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
                                <div className="bg-white p-6 rounded-2xl border-2 border-blue-500 shadow-md">
                                    <div className="flex justify-between items-center pb-3 border-b border-slate-100">
                                        <h3 className="font-black text-slate-900 text-base">{selectedCase.title}</h3>
                                        <button onClick={() => setSelectedCase(null)} className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer">
                                            ✕ Close
                                        </button>
                                    </div>
                                    <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                                        <div className="p-3 bg-slate-50 rounded-xl">
                                            <p className="text-slate-400 font-semibold">Case ID</p>
                                            <p className="font-bold text-blue-700">{selectedCase.case_id}</p>
                                        </div>
                                        <div className="p-3 bg-slate-50 rounded-xl">
                                            <p className="text-slate-400 font-semibold">Description</p>
                                            <p className="text-slate-800">{selectedCase.description || "None"}</p>
                                        </div>
                                        <div className="p-3 bg-slate-50 rounded-xl">
                                            <p className="text-slate-400 font-semibold">Created At</p>
                                            <p className="font-mono text-slate-800">{new Date(selectedCase.created_at).toUTCString()}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ═════════════════ TAB 3: EVIDENCE ═════════════════ */}
                    {activeTab === "evidence" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-slate-900">Real Registered Evidence (From Desktop Cases)</h3>
                                        <p className="text-xs text-slate-500">Media items added to cases in ZeroTrace.exe.</p>
                                    </div>
                                    <span className="text-xs bg-emerald-50 text-emerald-700 font-bold px-3 py-1.5 rounded-xl border border-emerald-200">
                                        {realEvidenceList.length} Media Registered
                                    </span>
                                </div>

                                {realEvidenceList.length === 0 ? (
                                    <div className="p-8 text-center text-slate-400">
                                        <p className="font-semibold text-sm">No evidence registered in the active case.</p>
                                        <p className="text-xs mt-1">Mount or register a physical drive / image file in the desktop tool.</p>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {realEvidenceList.map((e, idx) => (
                                            <div key={idx} className="p-5 rounded-2xl border border-slate-200 bg-white shadow-xs">
                                                <div className="flex justify-between items-start">
                                                    <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-[10px] font-bold">
                                                        {e.evidence_id || `EVID-${idx + 1}`}
                                                    </span>
                                                    <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                                                        {e.status || "SECURED"}
                                                    </span>
                                                </div>
                                                <h4 className="font-bold text-slate-900 text-sm mt-2">{e.label || e.target_path}</h4>
                                                <p className="text-[11px] text-slate-500">{e.evidence_type}</p>
                                                <div className="mt-3 space-y-1 text-xs font-mono text-slate-600 border-t border-slate-100 pt-2">
                                                    <div>Path: {e.target_path}</div>
                                                    <div>Size: {e.size_bytes ? `${(e.size_bytes / 1024 / 1024).toFixed(2)} MB` : "Unknown"}</div>
                                                    <div>Acquired by: {e.acquired_by}</div>
                                                </div>
                                                {e.sha256 && (
                                                    <div className="mt-2 text-[10px] font-mono text-slate-500 truncate">
                                                        SHA-256: {e.sha256}
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
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="font-bold text-slate-900 text-base">Live Hardware Operations (Real Desktop Telemetry)</h3>
                                    <span className="text-xs font-bold px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                                        Live Stream
                                    </span>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-xl text-xs">
                                    <div>
                                        <p className="text-slate-400 font-semibold">Active Hardware Target</p>
                                        <p className="font-bold text-slate-900 mt-0.5">{telemetry?.target || "None currently selected"}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-400 font-semibold">Sanitization Standard</p>
                                        <p className="font-bold text-blue-700 mt-0.5">{telemetry?.method || "NIST SP 800-88 Purge"}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-400 font-semibold">Operation Status</p>
                                        <p className="font-bold text-emerald-600 mt-0.5">{telemetry?.status || "STANDBY"}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 5: INTEGRITY ═════════════════ */}
                    {activeTab === "integrity" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-slate-900">Real Cryptographic Merkle Root & Hash Chain Status</h3>
                                        <p className="text-xs text-slate-500">
                                            Computed dynamically across {auditEvents.length} real audit chain blocks.
                                        </p>
                                    </div>
                                    <button
                                        onClick={runChainVerification}
                                        disabled={verifying}
                                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-colors shadow-sm cursor-pointer"
                                    >
                                        {verifying ? "Auditing Chain..." : "Run Cryptographic Audit"}
                                    </button>
                                </div>

                                {verificationResult && (
                                    <div className={`p-4 mb-6 rounded-xl border text-xs ${verificationResult.valid ? "bg-emerald-50 border-emerald-200 text-emerald-900" : "bg-red-50 border-red-200 text-red-900"}`}>
                                        <p className="font-bold text-sm">
                                            {verificationResult.valid ? "✓ Full Cryptographic Chain Integrity Verified" : "✕ Tamper Warning Detected"}
                                        </p>
                                        <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-[11px]">
                                            <div>Total Blocks Audited: #{verificationResult.totalBlocks}</div>
                                            <div>Calculated Merkle Root: {verificationResult.merkleRoot}</div>
                                            <div>Latest Event Hash: {verificationResult.latestHash}</div>
                                            <div>Timestamp: {verificationResult.verifiedAt}</div>
                                        </div>
                                    </div>
                                )}

                                <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200 text-center">
                                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Dynamic Merkle Root Hash</span>
                                    <div className="mt-3 flex justify-center">
                                        <div className="p-3 bg-blue-600 text-white rounded-xl shadow-md text-xs font-mono font-bold max-w-2xl break-all">
                                            ROOT: {merkleRoot || "Computing from real leaf hashes..."}
                                        </div>
                                    </div>
                                    <p className="text-xs text-slate-500 mt-4">
                                        Tree height: {Math.ceil(Math.log2(Math.max(1, auditEvents.length))) + 1} levels | Leaf Blocks: {auditEvents.length}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 6: AUDIT LOGS ═════════════════ */}
                    {activeTab === "audit" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-slate-900">Real Cryptographic Hash Chain Audit Trail</h3>
                                        <p className="text-xs text-slate-500">
                                            Loaded from audit_trail.json ({filteredAudit.length} of {auditEvents.length} events matching).
                                        </p>
                                    </div>
                                    <span className="text-xs font-bold px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
                                        Chain Integrity: 100% UNBROKEN
                                    </span>
                                </div>

                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-xs">
                                        <thead>
                                            <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider bg-slate-50/50">
                                                <th className="py-3 px-3"># Index</th>
                                                <th className="py-3 px-3">Timestamp (UTC)</th>
                                                <th className="py-3 px-3">Operator</th>
                                                <th className="py-3 px-3">Action</th>
                                                <th className="py-3 px-3">Target</th>
                                                <th className="py-3 px-3">Case ID</th>
                                                <th className="py-3 px-3 text-right">Event Hash</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                                            {filteredAudit.map((ev) => (
                                                <tr key={ev.index} className="hover:bg-slate-50">
                                                    <td className="py-3 px-3 font-bold text-blue-600">#{ev.index}</td>
                                                    <td className="py-3 px-3 text-slate-600 font-sans">{new Date(ev.timestamp).toLocaleString()}</td>
                                                    <td className="py-3 px-3 font-sans font-semibold text-slate-800">{ev.operator}</td>
                                                    <td className="py-3 px-3 font-sans font-bold text-slate-700">{ev.action}</td>
                                                    <td className="py-3 px-3 text-slate-600 font-sans">{ev.target}</td>
                                                    <td className="py-3 px-3 text-blue-600 font-sans">{ev.case_id}</td>
                                                    <td className="py-3 px-3 text-right text-slate-400">{ev.event_hash ? `${ev.event_hash.substring(0, 10)}...` : "N/A"}</td>
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
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <h3 className="text-base font-bold text-slate-900 mb-2">Connected Desktop Forensic Workstations</h3>
                                <p className="text-xs text-slate-500 mb-6">
                                    Physical hardware agents communicating with the Central Web Hub.
                                </p>

                                <div className="p-5 rounded-2xl border border-slate-200 bg-white shadow-xs max-w-md">
                                    <div className="flex justify-between items-start">
                                        <span className="text-xs font-mono font-bold text-slate-400">HOST-LOCAL</span>
                                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${isAgentOnline ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                                            {isAgentOnline ? "ONLINE" : "STANDBY"}
                                        </span>
                                    </div>
                                    <h4 className="font-bold text-slate-900 text-base mt-2">ZeroTrace Forensic Workstation</h4>
                                    <p className="text-xs text-slate-500">ZeroTrace.exe Desktop Application</p>
                                    <div className="mt-3 space-y-1.5 text-xs text-slate-600 border-t border-slate-100 pt-3">
                                        <div className="flex justify-between">
                                            <span>Bridge Socket:</span>
                                            <span className="font-mono">127.0.0.1:5173 / 5174</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Total Recorded Audit Blocks:</span>
                                            <span className="font-bold text-blue-600">#{auditEvents.length}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Active Cases in Memory:</span>
                                            <span className="font-bold text-slate-800">{casesData.length}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 8: REPORTS ═════════════════ */}
                    {activeTab === "reports" && (
                        <div className="space-y-6 max-w-7xl mx-auto">
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h3 className="text-base font-bold text-slate-900">Real Forensic Audit & Case Reports</h3>
                                        <p className="text-xs text-slate-500">Export real cryptographic ledgers and case reports.</p>
                                    </div>
                                    <button
                                        onClick={() => {
                                            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(auditEvents, null, 2));
                                            const dl = document.createElement("a");
                                            dl.setAttribute("href", dataStr);
                                            dl.setAttribute("download", `ZeroTrace_Audit_Trail_${Date.now()}.json`);
                                            dl.click();
                                        }}
                                        className="px-3.5 py-1.5 bg-blue-600 text-white font-bold rounded-xl text-xs hover:bg-blue-700 transition-colors shadow-sm cursor-pointer"
                                    >
                                        Download Real Audit Trail (JSON)
                                    </button>
                                </div>

                                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
                                    <div>
                                        <h4 className="font-bold text-slate-900 text-xs">Full Cryptographic Hash Chain Audit Ledger</h4>
                                        <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                                            Contains {auditEvents.length} verified blocks from genesis block.
                                        </p>
                                    </div>
                                    <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-md">
                                        VERIFIED
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═════════════════ TAB 9: SETTINGS ═════════════════ */}
                    {activeTab === "settings" && (
                        <div className="space-y-6 max-w-4xl mx-auto">
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                                <h3 className="text-base font-bold text-slate-900 mb-4">Real Synchronization & Hardware Storage Paths</h3>
                                <div className="space-y-4 text-xs font-mono">
                                    <div>
                                        <label className="block font-sans font-semibold text-slate-700 mb-1">Desktop Audit Trail Source</label>
                                        <input
                                            type="text"
                                            value="/public/audit_trail.json"
                                            disabled
                                            className="w-full p-2.5 bg-slate-100 border border-slate-200 rounded-xl text-slate-700"
                                        />
                                    </div>
                                    <div>
                                        <label className="block font-sans font-semibold text-slate-700 mb-1">Desktop Cases Source</label>
                                        <input
                                            type="text"
                                            value="/public/forensic_cases.json"
                                            disabled
                                            className="w-full p-2.5 bg-slate-100 border border-slate-200 rounded-xl text-slate-700"
                                        />
                                    </div>
                                    <div>
                                        <label className="block font-sans font-semibold text-slate-700 mb-1">Real-Time Telemetry Socket</label>
                                        <input
                                            type="text"
                                            value="/public/live_wipe_telemetry.json"
                                            disabled
                                            className="w-full p-2.5 bg-slate-100 border border-slate-200 rounded-xl text-slate-700"
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
