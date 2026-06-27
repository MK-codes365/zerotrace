import React from "react";
import Hero from "../components/Hero";
import Features from "../components/Features";
import DownloadSection from "../components/DownloadSection";
import TrustedBy from "../components/TrustedBy";
import WipeSimulator from "../components/WipeSimulator";
import ProcessFlow from "../components/ProcessFlow";
import ComparisonTable from "../components/ComparisonTable";
import StatsCounter from "../components/StatsCounter";
import Pricing from "../components/Pricing";

const Home = () => {
  return (
    <>
      <Hero />
      <TrustedBy />
      <WipeSimulator />
      <Features />
      <StatsCounter />
      <ProcessFlow />
      <ComparisonTable />
      <Pricing />
      <DownloadSection />
    </>
  );
};

export default Home;
