import React from "react";
import Hero from "./components/Hero";
import Features from "./components/Features";
import DownloadSection from "./components/DownloadSection";
import Footer from "./components/Footer";

function App() {
  return (
    <div className="App">
      <Hero />
      <Features />
      <DownloadSection />
      <Footer />
    </div>
  );
}

export default App;
