import React from "react";

const CtaSection = ({ onOpenDashboard }) => {
    return (
        <section id="cta" className="w-full py-24 px-6 md:px-8 bg-[#181717]">
            <div className="max-w-4xl mx-auto text-center space-y-6">
                <p className="text-[.7rem] text-[#eae5dd]">
                    Enterprise Defense Platform
                </p>

                <h2 className="text-4xl sm:text-6xl md:text-7xl font-bold text-[#f4efe7] tracking-tighter leading-[0.95]">
                    One Platform.
                    <br />
                    <span className="text-[#b1a696]">
                        Complete Evidence Lifecycle.
                    </span>
                </h2>

                <p className="text-base sm:text-lg text-[#b1a696] max-w-xl mx-auto leading-relaxed">
                    Deploy NIST-compliant media sanitization and deep forensic
                    file carving across air-gapped workstations or distributed
                    cloud clusters.
                </p>

                <div className="flex flex-wrap items-center justify-center gap-3 pt-6">
                    <button
                        onClick={onOpenDashboard}
                        className="px-8 py-4 rounded-full font-bold text-sm text-[#181717] bg-[#f4efe7] hover:bg-[#b1a696] transition-all hover:scale-105 flex items-center gap-2 cursor-pointer"
                    >
                        <span>Launch Platform Dashboard</span>
                    </button>

                    <a
                        href="/ZeroTrace.exe"
                        download="ZeroTrace.exe"
                        className="px-8 py-4 rounded-full font-bold text-sm text-[#f4efe7] border border-[#b1a696]/40 hover:bg-[#f4efe7]/10 transition-all flex items-center gap-2 cursor-pointer"
                    >
                        <span>Download Standalone (.EXE)</span>
                    </a>

                    <a
                        href="/ZeroTrace-Setup.msi"
                        download="ZeroTrace-Setup.msi"
                        className="px-8 py-4 rounded-full font-bold text-sm text-[#b1a696] border border-[#b1a696]/40 hover:bg-[#b1a696]/10 transition-all flex items-center gap-2 cursor-pointer"
                    >
                        <span>Download Installer (.MSI)</span>
                    </a>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-[#b1a696] pt-8">
                    <a
                        href="http://localhost:8000/docs"
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-[#f4efe7] transition-colors"
                    >
                        API Gateway (/docs)
                    </a>
                    <span className="text-[#524e4b]">·</span>
                    <a
                        href="https://github.com/MK-codes365/zerotrace"
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-[#f4efe7] transition-colors"
                    >
                        GitHub Repository
                    </a>
                    <span className="text-[#524e4b]">·</span>
                    <span className="text-[#f4efe7]">
                        NIST SP 800-88 & ISO/IEC 27037
                    </span>
                </div>
            </div>
        </section>
    );
};

export default CtaSection;
