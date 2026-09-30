import React from "react";

const Footer = ({ onOpenDashboard, onScrollToSection }) => {
    return (
        <section className="w-screen min-h-dvh px-6 mt-10 bg-[#181717] relative">
            <p className="text-[.7rem] text-[#eae5dd] mt-10">
                Ready to secure your digital evidence?
                <br />
                Deploy ZeroTrace<span>®</span> now
            </p>

            {/* Marquee */}
            <div className="w-full overflow-hidden mt-8 mb-14">
                <div className="marquee-track">
                    {[...Array(4)].map((_, i) => (
                        <span
                            key={i}
                            className="text-[#f4efe7] text-[8vw] font-bold tracking-tighter whitespace-nowrap px-4"
                        >
                            SANITIZE · RECOVER · VERIFY · PROTECT ·{" "}
                        </span>
                    ))}
                </div>
            </div>

            <div className="flex flex-col lg:flex-row justify-between items-start text-2xl gap-10">
                <h3 className="text-[#b1a696] lg:w-1/2">
                    ZeroTrace® provides military-grade
                    <br />
                    data sanitization and forensic-grade
                    <br />
                    file recovery—for defense and
                    <br />
                    enterprise deployments.
                    <br />
                    <br />
                    <button
                        onClick={onOpenDashboard}
                        className="text-[#f4efe7] hover:text-[#b1a696] underline cursor-pointer text-2xl"
                    >
                        Launch Dashboard
                    </button>
                </h3>

                <div className="flex flex-col justify-center items-end gap-1">
                    {[
                        { id: "hero", label: "Home" },
                        { id: "features", label: "Features" },
                        { id: "how-it-works", label: "Pipeline" },
                        { id: "use-cases", label: "Use Cases" },
                        { id: "download", label: "Download" },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => onScrollToSection(item.id)}
                            className="text-[#f2ede5] text-2xl hover:text-[#b1a696] transition-colors cursor-pointer text-right"
                        >
                            {item.label}
                        </button>
                    ))}
                </div>
            </div>

            <div className="w-full flex flex-col sm:flex-row justify-between items-center mt-20 gap-4 pb-8">
                <div className="flex justify-center items-center gap-1">
                    <a
                        href="https://github.com/MK-codes365/zerotrace"
                        target="_blank"
                        rel="noreferrer"
                        className="border-[1px] border-[#c4c1b9] rounded-full p-3 text-[#f2ede5] hover:bg-[#f2ede5]/10 transition-colors"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                        </svg>
                    </a>
                    <a
                        href="http://localhost:8000/docs"
                        target="_blank"
                        rel="noreferrer"
                        className="border-[1px] border-[#c4c1b9] rounded-full p-3 text-[#f2ede5] hover:bg-[#f2ede5]/10 transition-colors"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                            <line x1="16" y1="13" x2="8" y2="13" />
                            <line x1="16" y1="17" x2="8" y2="17" />
                            <polyline points="10 9 9 9 8 9" />
                        </svg>
                    </a>
                </div>

                <div>
                    <p className="text-[0.8rem] text-[#b1a696] text-right">
                        © 2026 ZeroTrace® · Integrated Secure Data
                        <br />
                        Erasure & Digital Forensic Recovery Platform.
                    </p>
                </div>
            </div>

            {/* Footer Title */}
            <div className="relative w-full h-[30vh] border-t border-[#c4c1b9]/20 overflow-hidden">
                <div className="w-full flex justify-between items-center px-0 mt-8">
                    <p className="text-[#b1a696] text-[0.7rem]">
                        NIST SP 800-88 · ISO/IEC 27037
                    </p>
                    <p className="text-[#b1a696] text-[0.7rem]">
                        All rights reserved ©{" "}
                        <span className="text-[#f2ede5]">2026</span>
                    </p>
                </div>

                <div className="footer-title">
                    <h1 className="text-[18vw] font-bold text-[#f4efe7]">
                        ZeroTrace<sub>®</sub>
                    </h1>
                </div>
            </div>
        </section>
    );
};

export default Footer;
