import React from 'react';
import { Link } from 'react-router-dom';
import './About.css';

const About = () => {
  return (
    <div className="about-page">
      {/* Navigation placeholder if not global - assuming global nav exists, but adding back link just in case */}
      <nav style={{ position: 'absolute', top: 20, left: 20, zIndex: 20 }}>
        <Link to="/" style={{ color: 'white', opacity: 0.8, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>←</span> Back
        </Link>
      </nav>

      <section className="about-hero">
        <div className="about-hero-content">
          <h1>ZEROTRACE</h1>
          <p>Digital sovereignty reimagined</p>
        </div>
      </section>

      <div className="container">
        <section className="about-section mission-section">
          <div className="mission-content">
            <h2>Our Mission</h2>
            <p>
              In a digital age where data privacy is constantly under threat, ZeroTrace was born from a simple yet powerful idea: you should have complete control over your digital footprint. We provide tools that empower individuals and organizations to securely act on their right to be forgotten.
            </p>
          </div>
        </section>

        <section className="about-section">
          <h2>The Technology</h2>
          <div className="tech-grid">
            <div className="tech-card">
              <h3>DOD 5220.22-M</h3>
              <p>Standard data sanitization method used by the US Department of Defense. We implement the 3-pass overwrite standard.</p>
            </div>
            <div className="tech-card">
              <h3>Gutmann Method</h3>
              <p>For extreme security, we offer the 35-pass algorithm developed by Peter Gutmann, ensuring recovery is theoretically impossible.</p>
            </div>
            <div className="tech-card">
              <h3>NIST SP 800-88</h3>
              <p>Modern media sanitization guidelines compliant with current federal standards for media destruction.</p>
            </div>
          </div>
        </section>
      </div>

      <section className="about-section open-source-section">
        <div className="container">
          <h2>Open Source Promise</h2>
          <p>
            Transparency is the key to trust. That's why ZeroTrace is and will always be open source. We believe that security tools should be verifiable by the community, ensuring no backdoors and complete integrity in our operations.
          </p>
          <div className="contact-actions">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="btn-primary">View on GitHub</a>
          </div>
        </div>
      </section>

      <section className="about-section">
        <h2>Get in Touch</h2>
        <p>
          Have questions regarding enterprise integration or custom solutions?
        </p>
        <div className="contact-actions">
          <a href="mailto:hello@zerotrace.com" className="btn-secondary">Contact Support</a>
        </div>
      </section>

      <footer style={{ textAlign: 'center', padding: '40px', color: '#555', borderTop: '1px solid #111' }}>
        <p>&copy; {new Date().getFullYear()} ZeroTrace. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default About;
