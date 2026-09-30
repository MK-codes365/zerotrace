import React from "react";
import gsap from "gsap/all";
import { useGSAP } from "@gsap/react";
import { useMediaQuery } from "react-responsive";

const HeroSection = ({ onOpenDashboard }) => {
    const isMobile = useMediaQuery({ query: "(max-width:768px)" });

    useGSAP(() => {
        if (!isMobile) {
            gsap.to(".hero-section .hero-video", {
                yPercent: -6,
                scale: 1.15,
                ease: "power1.inOut",
                force3D: true,
                scrollTrigger: {
                    trigger: ".hero-section",
                    start: "top top",
                    end: "bottom top",
                    scrub: 1.2,
                },
            });
        }
    }, [isMobile]);

    return (
        <section className="hero-section w-dvw md:h-dvh h-[100vh] md:p-2 p-2.5 mb-20">
            <div className="relative w-full h-full rounded-[2.5rem] overflow-hidden bg-[#181717]">
                {/* 60 FPS Hardware-Accelerated Video background */}
                <video
                    autoPlay
                    loop
                    muted
                    playsInline
                    preload="auto"
                    disablePictureInPicture
                    disableRemotePlayback
                    className="hero-video absolute inset-0 w-full h-full object-cover z-0 will-change-transform transform-gpu translate-z-0"
                    style={{
                        transform: "translate3d(0, 0, 0)",
                        backfaceVisibility: "hidden",
                        WebkitBackfaceVisibility: "hidden",
                    }}
                >
                    <source src="/hero.mp4" type="video/mp4" />
                    <source src="/Hero.mp4" type="video/mp4" />
                </video>

                {/* Ambient dark gradient overlay for optimal text contrast */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#181717]/80 via-[#181717]/30 to-[#181717]/60 z-[5] pointer-events-none" />

                <div className="p-4 flex flex-col md:justify-center relative z-10">
                    <div className="relative h-dvh">
                        <h1
                            className="text-[#f4efe7] text-start text-6xl md:text-9xl font-bold tracking-wider lg:absolute lg:left-2"
                            style={{ textShadow: "2px 2px 4px rgba(0,0,0,0.5)" }}
                        >
                            ZeroTrace®
                        </h1>

                        <div className="w-full h-auto absolute top-24 md:bottom-[8%] lg:bottom-[9%] flex md:flex-row flex-col md:justify-between md:items-end">
                            <h2
                                className="text-start lg:mt-0 md:text-[#f4efe7] text-[#b1a696] text-2xl font-bold md:tracking-wider leading-5 flex flex-col gap-1"
                                style={{ textShadow: "2px 2px 4px #000" }}
                            >
                                <span>Defensive</span>
                                <span>Sanitization—Forensic</span>
                                <span>Recovery</span>
                            </h2>

                            <p
                                className="md:w-[20%] w-[80%] text-[#f4efe7] text-[0.7rem] font-bold md:font-medium tracking-wide lg:text-end mt-2 text-justify"
                                style={{ textShadow: "2px 2px 4px #000" }}
                            >
                                Military-grade data sanitization and forensic-grade file recovery.
                                Engineered for defense agencies and enterprise cybersecurity operations.
                            </p>
                        </div>

                        {/* Bottom Action Buttons */}
                        <div className="absolute bottom-8 left-0 right-0 flex flex-wrap items-center gap-3 md:px-2">
                            <button
                                onClick={onOpenDashboard}
                                className="px-6 py-3 rounded-full text-sm font-bold text-[#181717] bg-[#f4efe7] hover:bg-[#b1a696] transition-all cursor-pointer"
                            >
                                Launch Dashboard
                            </button>
                            <a
                                href="/ZeroTrace.exe"
                                download="ZeroTrace.exe"
                                className="px-6 py-3 rounded-full text-sm font-bold text-[#f4efe7] border border-[#f4efe7]/40 hover:bg-[#f4efe7]/10 transition-all"
                            >
                                Download .EXE
                            </a>
                            <a
                                href="/ZeroTrace-Setup.msi"
                                download="ZeroTrace-Setup.msi"
                                className="px-6 py-3 rounded-full text-sm font-bold text-[#b1a696] border border-[#b1a696]/40 hover:bg-[#b1a696]/10 transition-all"
                            >
                                Download .MSI
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default HeroSection;
