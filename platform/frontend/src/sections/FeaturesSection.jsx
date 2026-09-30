import React from "react";

const FeaturesSection = ({ onOpenDashboard }) => {
    const features = [
        {
            title: "Certified Secure Erasure",
            desc: "NIST SP 800-88 Clear & Purge, DoD 5220.22-M (3-pass/7-pass), and Gutmann 35-pass algorithms. Real-time 0x00 hex verification guarantees zero residual magnetization.",
            badge: "NIST SP 800-88",
        },
        {
            title: "Advanced File Carving",
            desc: "Signature-based recovery for 11+ file types (JPEG, PDF, DOCX, ZIP, MP4) with bi-directional fragment graph stitching to recover fragmented files without filesystem metadata.",
            badge: "11+ SIGNATURES",
        },
        {
            title: "Merkle Tree Integrity Proof",
            desc: "Every 4KB drive block is independently hashed into a hierarchical Merkle Tree. Provides instant O(log N) mathematical proof of evidence immutability.",
            badge: "TAMPER-PROOF",
        },
        {
            title: "Master-Worker MapReduce",
            desc: "Distributed compute architecture that splits multi-terabyte raw disk images into dynamic chunk slices for parallel processing across elastic worker pools.",
            badge: "HIGH THROUGHPUT",
        },
        {
            title: "Court-Admissible Reports",
            desc: "Automated generation of tamper-evident PDF sanitization certificates, forensic audit ledgers, and JSON verification records adhering to ISO/IEC 27037 standards.",
            badge: "ISO/IEC 27037",
        },
        {
            title: "Native C++ Windows Agent",
            desc: "Desktop agent written with native C++ DLLs for raw sector-level drive handles, automated WMI physical drive detection, and air-gapped offline operation.",
            badge: "WIN64 MSI",
        },
    ];

    return (
        <section
            id="features"
            className="w-full py-24 px-6 md:px-8 bg-[#181717]"
        >
            <div className="max-w-6xl mx-auto">
                {/* Section Header */}
                <div className="mb-16">
                    <p className="text-[.7rem] text-[#eae5dd] mb-4">
                        Core Capabilities
                    </p>
                    <h2 className="text-[#f4efe7] text-4xl md:text-6xl font-bold tracking-tighter leading-[0.95] mb-6">
                        Forensic &<br />
                        Sanitization Features
                    </h2>
                    <p className="text-[#b1a696] text-base md:text-lg max-w-xl leading-relaxed">
                        Engineered to meet national defense and enterprise
                        forensic-grade data sanitization standards.
                    </p>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {features.map((feat, idx) => (
                        <div
                            key={idx}
                            className="p-6 rounded-[2rem] bg-[#292725] hover:bg-[#2f2c29] transition-colors flex flex-col justify-between space-y-4 group"
                        >
                            <div>
                                <div className="flex items-center justify-between mb-5">
                                    <span className="text-[10px] text-[#f4efe7] px-3 py-1 rounded-full border border-[#b1a696]/30">
                                        {feat.badge}
                                    </span>
                                </div>
                                <h3 className="text-xl font-bold text-[#f4efe7] mb-3">
                                    {feat.title}
                                </h3>
                                <p className="text-sm text-[#b1a696] leading-relaxed">
                                    {feat.desc}
                                </p>
                            </div>

                            <button
                                onClick={onOpenDashboard}
                                className="text-xs text-[#f4efe7] hover:text-[#b1a696] transition-colors flex items-center gap-1.5 pt-2 text-left cursor-pointer group-hover:translate-x-1 transition-transform duration-300"
                            >
                                <span>Inspect in Dashboard →</span>
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default FeaturesSection;
