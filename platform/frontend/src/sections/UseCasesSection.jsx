import React from "react";

const UseCasesSection = ({ onOpenDashboard }) => {
    const useCases = [
        {
            title: "Defense & Intelligence Agencies",
            tag: "MILITARY-GRADE",
            desc: "Secure sanitization of top-secret storage media before physical disposal, and deep forensic reconstruction of captured adversary drives without filesystem metadata.",
            bulletPoints: [
                "NIST SP 800-88 Purge & DoD 5220.22-M 7-Pass ECE",
                "Air-gapped operation with offline C++ native agent",
                "Zero residual magnetic remanence verification",
            ],
        },
        {
            title: "Law Enforcement & Digital Forensics",
            tag: "JUDICIAL ADMISSIBILITY",
            desc: "Extracting critical deleted evidence from seized drives with complete ISO/IEC 27037 chain-of-custody logging and cryptographic Merkle tree non-repudiation.",
            bulletPoints: [
                "Tamper-evident SHA-256 hash-chained audit trails",
                "Signature carving across 11+ evidence file formats",
                "Court-ready PDF certificate and JSON data export",
            ],
        },
        {
            title: "Enterprise IT Asset Disposition",
            tag: "REGULATORY COMPLIANCE",
            desc: "Guarantees corporate compliance with data privacy regulations (GDPR, HIPAA, ISO 27001) when recycling, reallocating, or retiring employee workstations and data center servers.",
            bulletPoints: [
                "Automated WMI drive serial and model detection",
                "Certified PDF certificates with SHA-256 seal",
                "Eliminates corporate liability from data leakage",
            ],
        },
        {
            title: "Incident Response & Malware Labs",
            tag: "THREAT HUNTING",
            desc: "Reconstructing fragmented payloads and malicious executables from raw memory dumps, damaged partition tables, and unallocated cluster spaces.",
            bulletPoints: [
                "Bi-directional fragment graph reconstruction",
                "Entropy & heuristic structure validation",
                "Fast MapReduce processing on large disk images",
            ],
        },
    ];

    return (
        <section
            id="use-cases"
            className="w-full py-24 px-6 md:px-8 bg-[#181717]"
        >
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-16">
                    <p className="text-[.7rem] text-[#eae5dd] mb-4">
                        Operational Applications
                    </p>
                    <h2 className="text-[#f4efe7] text-4xl md:text-6xl font-bold tracking-tighter leading-[0.95] mb-6">
                        Industry Use Cases
                    </h2>
                    <p className="text-[#b1a696] text-base md:text-lg max-w-xl leading-relaxed">
                        Deployed across national intelligence infrastructure,
                        cyber defense wings, and enterprise forensic teams.
                    </p>
                </div>

                {/* Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {useCases.map((uc, i) => (
                        <div
                            key={i}
                            className="p-7 rounded-[2rem] bg-[#292725] hover:bg-[#2f2c29] transition-colors flex flex-col justify-between space-y-4 group"
                        >
                            <div>
                                <div className="flex items-center justify-between mb-4">
                                    <span className="text-[10px] text-[#f4efe7] px-3 py-1 rounded-full border border-[#b1a696]/30">
                                        {uc.tag}
                                    </span>
                                </div>

                                <h3 className="text-xl font-bold text-[#f4efe7] mb-2">
                                    {uc.title}
                                </h3>

                                <p className="text-sm text-[#b1a696] leading-relaxed mb-4">
                                    {uc.desc}
                                </p>

                                <ul className="space-y-2 text-xs text-[#b1a696]">
                                    {uc.bulletPoints.map((bp, j) => (
                                        <li
                                            key={j}
                                            className="flex items-center gap-2"
                                        >
                                            <span className="w-1 h-1 rounded-full bg-[#f4efe7] flex-shrink-0" />
                                            <span>{bp}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div className="pt-2">
                                <button
                                    onClick={onOpenDashboard}
                                    className="text-xs text-[#f4efe7] hover:text-[#b1a696] transition-colors flex items-center gap-1.5 cursor-pointer"
                                >
                                    <span>
                                        Open Console for this Workflow →
                                    </span>
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default UseCasesSection;
