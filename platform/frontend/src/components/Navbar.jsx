import React, { useState } from "react";

const Navbar = ({ onOpenDashboard, onScrollToSection }) => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const handleNav = (id) => {
        setMobileMenuOpen(false);
        if (onScrollToSection) onScrollToSection(id);
    };

    const navLinks = [
        { id: "features", label: "Features" },
        { id: "how-it-works", label: "Pipeline" },
        { id: "use-cases", label: "Use Cases" },
        { id: "download", label: "Download" },
    ];

    return (
        <header className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center">
            {/* Mobile Dropdown Menu (Floats above the bar) */}
            {mobileMenuOpen && (
                <div
                    className="mb-3 w-72 rounded-3xl p-4 shadow-2xl flex flex-col gap-1.5 animate-in fade-in slide-in-from-bottom-3 duration-200"
                    style={{
                        backgroundColor: "#f4efe7",
                        color: "#181717",
                        border: "1px solid rgba(42, 39, 37, 0.15)",
                    }}
                >
                    <div className="flex items-center justify-between pb-2 border-b border-[#2a2725]/15 px-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-[#2a2725]/70">
                            Navigation
                        </span>
                        <button
                            onClick={() => setMobileMenuOpen(false)}
                            className="text-xs font-bold text-[#2a2725]/60 hover:text-[#2a2725] cursor-pointer"
                        >
                            Close ✕
                        </button>
                    </div>

                    {navLinks.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => handleNav(item.id)}
                            className="text-left font-semibold text-sm px-3.5 py-2.5 rounded-2xl transition-colors cursor-pointer hover:bg-[#2a2725]/10"
                            style={{ color: "#181717" }}
                        >
                            {item.label}
                        </button>
                    ))}

                    <div className="pt-2 border-t border-[#2a2725]/15 flex flex-col gap-1.5 mt-1">
                        <button
                            onClick={() => {
                                setMobileMenuOpen(false);
                                onOpenDashboard();
                            }}
                            className="w-full py-2.5 px-4 rounded-2xl font-bold text-xs text-center cursor-pointer transition-colors"
                            style={{ backgroundColor: "#181717", color: "#f4efe7" }}
                        >
                            Launch Dashboard →
                        </button>
                        <a
                            href="/ZeroTrace.exe"
                            download="ZeroTrace.exe"
                            className="w-full py-2 px-4 rounded-2xl font-medium text-xs text-center border border-[#2a2725]/20 hover:bg-[#2a2725]/5 transition-colors block"
                            style={{ color: "#181717" }}
                        >
                            Download Standalone (.EXE)
                        </a>
                        <a
                            href="/ZeroTrace-Setup.msi"
                            download="ZeroTrace-Setup.msi"
                            className="w-full py-2 px-4 rounded-2xl font-medium text-xs text-center border border-[#2a2725]/20 hover:bg-[#2a2725]/5 transition-colors block"
                            style={{ color: "#181717" }}
                        >
                            Download Installer (.MSI)
                        </a>
                    </div>
                </div>
            )}

            {/* Main Floating Navbar Pill */}
            <nav
                className="flex items-center gap-1.5 sm:gap-2 px-2 py-1.5 rounded-full shadow-[0_12px_36px_rgba(0,0,0,0.45)] backdrop-blur-md transition-colors duration-200"
                style={{
                    backgroundColor: "#f4efe7",
                    color: "#181717",
                    border: "1px solid rgba(255, 255, 255, 0.3)",
                }}
            >
                {/* Brand / Logo */}
                <button
                    onClick={() => handleNav("hero")}
                    className="flex items-center gap-2 pl-3 pr-2 py-1 rounded-full hover:bg-[#2a2725]/8 transition-colors cursor-pointer"
                    style={{ color: "#181717" }}
                    title="ZeroTrace Home"
                >
                    <img
                        src="/logo.png"
                        alt="ZeroTrace Logo"
                        width="20"
                        height="20"
                        className="w-5 h-5 object-contain rounded-sm shrink-0"
                    />
                    <span
                        className="text-xs sm:text-sm font-black tracking-tight"
                        style={{ color: "#181717" }}
                    >
                        ZeroTrace<span className="text-[10px] align-super">®</span>
                    </span>
                </button>

                {/* Divider */}
                <div className="h-4 w-[1px] bg-[#2a2725]/20 hidden md:block" />

                {/* Desktop Nav Links */}
                <div className="hidden md:flex items-center gap-0.5">
                    {navLinks.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => handleNav(item.id)}
                            className="text-xs font-semibold px-3 py-1.5 rounded-full transition-all cursor-pointer hover:bg-[#2a2725]/10 active:scale-95"
                            style={{ color: "#2a2725" }}
                        >
                            {item.label}
                        </button>
                    ))}
                </div>

                {/* Divider */}
                <div className="h-4 w-[1px] bg-[#2a2725]/20" />

                {/* Dashboard Action Button */}
                <button
                    onClick={onOpenDashboard}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold transition-all shadow-sm hover:opacity-90 active:scale-95 cursor-pointer"
                    style={{
                        backgroundColor: "#181717",
                        color: "#f4efe7",
                    }}
                >
                    <span>Dashboard</span>
                    <svg
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <polyline points="9 18 15 12 9 6" />
                    </svg>
                </button>

                {/* Mobile Menu Toggle Button */}
                <button
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    className="md:hidden flex items-center justify-center w-8 h-8 rounded-full transition-transform duration-300 hover:rotate-90 active:scale-90 cursor-pointer"
                    style={{
                        backgroundColor: "#2a2725",
                        color: "#b1a696",
                    }}
                    aria-label="Toggle navigation menu"
                >
                    {mobileMenuOpen ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <line x1="4" y1="6" x2="20" y2="6" />
                            <line x1="4" y1="12" x2="20" y2="12" />
                            <line x1="4" y1="18" x2="20" y2="18" />
                        </svg>
                    )}
                </button>
            </nav>
        </header>
    );
};

export default Navbar;
