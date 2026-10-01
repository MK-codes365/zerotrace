import React, { useState, useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import Navbar from "../components/Navbar";
import HeroSection from "../sections/HeroSection";
import WelcomeSection from "../sections/WelcomeSection";
import ChooseSection from "../sections/ChooseSection";
import StickyColsSection from "../sections/StickyColsSection";
import FeaturesSection from "../sections/FeaturesSection";
import HowItWorksSection from "../sections/HowItWorksSection";
import UseCasesSection from "../sections/UseCasesSection";
import DownloadSection from "../sections/DownloadSection";
import CtaSection from "../sections/CtaSection";
import Footer from "../components/Footer";
import DashboardView from "../components/DashboardView";

gsap.registerPlugin(ScrollTrigger);

const Home = () => {
    const [viewMode, setViewMode] = useState("landing");

    const scrollToSection = (id) => {
        if (viewMode !== "landing") {
            setViewMode("landing");
            setTimeout(() => {
                const el = document.getElementById(id);
                el?.scrollIntoView({ behavior: "smooth" });
            }, 100);
        } else {
            const el = document.getElementById(id);
            el?.scrollIntoView({ behavior: "smooth" });
        }
    };

    // Refresh ScrollTrigger when switching to landing
    useEffect(() => {
        if (viewMode === "landing") {
            setTimeout(() => {
                ScrollTrigger.refresh();
            }, 200);
        }
    }, [viewMode]);

    if (viewMode === "dashboard") {
        return <DashboardView onBackToLanding={() => setViewMode("landing")} />;
    }

    return (
        <div className="bg-[#181717] text-[#f4efe7] min-h-screen selection:bg-[#f4efe7] selection:text-[#181717] font-sans">
            {/* Floating Bottom Navbar */}
            <Navbar
                onOpenDashboard={() => setViewMode("dashboard")}
                onScrollToSection={scrollToSection}
            />

            {/* Main Content Landmark for Accessibility & Agentic Crawlers */}
            <main id="main-content" role="main">
                {/* Hero - Capsule style rounded card with video */}
                <HeroSection onOpenDashboard={() => setViewMode("dashboard")} />

                {/* Welcome - Clip-path text reveal on scroll */}
                <WelcomeSection />

                {/* Choose - Gradient section with clip title reveal */}
                <ChooseSection onOpenDashboard={() => setViewMode("dashboard")} />

                {/* Sticky Columns - Pinned multi-column animation */}
                <StickyColsSection />

                {/* Features Grid */}
                <FeaturesSection
                    onOpenDashboard={() => setViewMode("dashboard")}
                />

                {/* How It Works Pipeline */}
                <HowItWorksSection />

                {/* Use Cases */}
                <UseCasesSection
                    onOpenDashboard={() => setViewMode("dashboard")}
                />

                {/* Download Desktop Tool */}
                <DownloadSection />

                {/* Final CTA */}
                <CtaSection onOpenDashboard={() => setViewMode("dashboard")} />
            </main>

            {/* Footer */}
            <Footer
                onOpenDashboard={() => setViewMode("dashboard")}
                onScrollToSection={scrollToSection}
            />
        </div>
    );
};

export default Home;
