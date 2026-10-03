import React from "react";

const DownloadSection = () => {
    return (
        <section
            id="download"
            className="w-full py-24 px-6 md:px-8 bg-[#181717]"
        >
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="mb-12">
                    <p className="text-[.7rem] text-[#eae5dd] mb-4">
                        Offline Field Deployment
                    </p>
                    <h2 className="text-[#f4efe7] text-4xl md:text-6xl font-bold tracking-tighter leading-[0.95] mb-6">
                        Download Desktop Tool
                    </h2>
                    <p className="text-[#b1a696] text-base md:text-lg max-w-xl leading-relaxed">
                        Native Windows 64-bit application equipped with
                        low-level C++ disk drivers for raw sector sanitization
                        and offline digital forensic acquisition.
                    </p>
                </div>

                {/* Download Card */}
                <div className="p-8 sm:p-10 rounded-[2.5rem] bg-[#292725] border border-[#b1a696]/10">
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
                        {/* Left: Product Info */}
                        <div className="md:col-span-7 space-y-4">
                            <div className="flex items-center gap-3 flex-wrap">
                                <span className="px-3 py-1 rounded-full text-[#f4efe7] text-xs border border-[#b1a696]/30">
                                    VERSION 1.4.0 (STABLE)
                                </span>
                                <span className="text-xs text-[#b1a696]">
                                    Windows 10 / 11 / Server (x64)
                                </span>
                            </div>

                            <h3 className="text-2xl font-bold text-[#f4efe7]">
                                ZeroTrace Forensic Wiper & Recovery Agent
                            </h3>

                            <p className="text-sm text-[#b1a696] leading-relaxed">
                                Self-contained installer bundled with
                                high-performance C++ disk I/O routines, WMI
                                drive enumerator, and forensic PDF certificate
                                engine.
                            </p>

                            <div className="space-y-2 text-xs text-[#b1a696] pt-2">
                                {[
                                    "Direct \\\\.\\PhysicalDrive handle manipulation (0x00 verified)",
                                    "NIST 800-88 Clear/Purge, DoD 5220.22-M & Gutmann 35-pass",
                                    "Offline PDF sanitization certificate generation",
                                    "Automatic telemetry sync with platform backend (optional)",
                                ].map((item, i) => (
                                    <div
                                        key={i}
                                        className="flex items-center gap-2"
                                    >
                                        <span className="w-1 h-1 rounded-full bg-[#f4efe7] flex-shrink-0" />
                                        <span>{item}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right: Download Buttons */}
                        <div className="md:col-span-5 flex flex-col items-center justify-center p-6 rounded-[2rem] bg-[#1f1d1b] text-center space-y-4">
                            <div className="w-16 h-16 rounded-2xl bg-[#292725] border border-[#b1a696]/20 text-[#f4efe7] flex items-center justify-center text-3xl mb-1">
                                🖥️
                            </div>

                            <div>
                                <div className="text-base font-bold text-[#f4efe7]">
                                    ZeroTrace Desktop Engine
                                </div>
                                <div className="text-[11px] text-[#b1a696]">
                                    Windows 10 / 11 / Server (x64) · Direct
                                    Download
                                </div>
                            </div>

                            <a
                                href="/ZeroTrace.exe"
                                download="ZeroTrace.exe"
                                className="w-full py-3.5 rounded-full font-bold text-xs uppercase tracking-wider text-[#181717] bg-[#f4efe7] hover:bg-[#b1a696] transition-all hover:scale-105 flex items-center justify-center gap-2 cursor-pointer"
                            >
                                <span>Download Standalone (.EXE)</span>
                            </a>
                            <div className="text-[10px] text-[#b1a696] -mt-2">
                                ~39.2 MB · Portable (No installation required)
                            </div>

                            <a
                                href="/ZeroTrace-Setup.msi"
                                download="ZeroTrace-Setup.msi"
                                className="w-full py-2.5 rounded-full font-bold text-xs uppercase tracking-wider text-[#f4efe7] bg-transparent hover:bg-[#f4efe7]/10 border border-[#b1a696]/40 transition-all flex items-center justify-center gap-2 cursor-pointer"
                            >
                                <span>Download Installer (.MSI)</span>
                            </a>
                            <div className="text-[10px] text-[#b1a696] -mt-2">
                                ~31.7 MB · Desktop & Start Menu Shortcut
                            </div>

                            <div className="text-[10px] text-[#b1a696] pt-1">
                                Requires Administrator privileges for raw disk
                                handles.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default DownloadSection;
