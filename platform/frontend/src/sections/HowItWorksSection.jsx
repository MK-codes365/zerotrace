import React from "react";

const HowItWorksSection = () => {
    const steps = [
        {
            step: "01",
            title: "Evidence Acquisition",
            desc: "Physical storage media or raw forensic images (E01, DD, RAW) are acquired using write-blocking interfaces. Initial dual SHA-256 and SHA-512 hashes are calculated immediately.",
            sub: "Write-Blocked Ingest",
        },
        {
            step: "02",
            title: "Processing & Partitioning",
            desc: "The Master Controller dynamically divides multi-terabyte drives into partitioned chunk slices (Map phase) and assigns tasks to multi-threaded worker pools via Redis queues.",
            sub: "MapReduce Dispatch",
        },
        {
            step: "03",
            title: "Recovery or Erasure",
            desc: "Workers execute deep signature file carving with fragment graph reconstruction OR certified multi-pass overwriting (NIST SP 800-88 / DoD 5220.22-M).",
            sub: "Dual Engine Execution",
        },
        {
            step: "04",
            title: "Integrity Validation",
            desc: "Carved files undergo structure parsing and entropy validation with consensus scoring. Sanitized sectors undergo 100% hex readback to certify zero residual magnetization.",
            sub: "Hex Verification & Consensus",
        },
        {
            step: "05",
            title: "Forensic Reporting",
            desc: "Operations are committed to the tamper-evident SHA-256 hash chain. The platform exports cryptographically signed PDF sanitization certificates or forensic carving reports.",
            sub: "Audit Ledger & PDF Cert",
        },
    ];

    return (
        <section
            id="how-it-works"
            className="w-full py-24 px-6 md:px-8 bg-[#181717]"
        >
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-16">
                    <p className="text-[.7rem] text-[#eae5dd] mb-4">
                        Lifecycle Pipeline
                    </p>
                    <h2 className="text-[#f4efe7] text-4xl md:text-6xl font-bold tracking-tighter leading-[0.95] mb-6">
                        How It Works
                    </h2>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-[#b1a696]">
                        <span className="border border-[#b1a696]/30 px-3 py-1 rounded-full text-xs">
                            Evidence
                        </span>
                        <span className="text-[#524e4b]">→</span>
                        <span className="border border-[#b1a696]/30 px-3 py-1 rounded-full text-xs">
                            Processing
                        </span>
                        <span className="text-[#524e4b]">→</span>
                        <span className="border border-[#f4efe7]/30 px-3 py-1 rounded-full text-xs text-[#f4efe7]">
                            Recovery / Erasure
                        </span>
                        <span className="text-[#524e4b]">→</span>
                        <span className="border border-[#b1a696]/30 px-3 py-1 rounded-full text-xs">
                            Validation
                        </span>
                        <span className="text-[#524e4b]">→</span>
                        <span className="border border-[#b1a696]/30 px-3 py-1 rounded-full text-xs">
                            Report
                        </span>
                    </div>
                </div>

                {/* 5-Step List */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                    {steps.map((st, i) => (
                        <div
                            key={i}
                            className="p-5 rounded-[2rem] bg-[#292725] flex flex-col justify-between space-y-3 relative"
                        >
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-[#f4efe7] text-xl font-extrabold">
                                        {st.step}
                                    </span>
                                    <span className="text-[10px] text-[#b1a696] uppercase">
                                        STAGE {i + 1}
                                    </span>
                                </div>
                                <h3 className="text-base font-bold text-[#f4efe7] mb-1">
                                    {st.title}
                                </h3>
                                <div className="text-[11px] text-[#b1a696] border border-[#b1a696]/30 inline-block px-2 py-0.5 rounded-full mb-2">
                                    {st.sub}
                                </div>
                                <p className="text-xs text-[#b1a696] leading-relaxed">
                                    {st.desc}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default HowItWorksSection;
