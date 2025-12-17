import React from 'react';

const Hero = () => {
  const scrollToDownloads = () => {
    document.getElementById('downloads').scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section style={styles.heroSection}>
      <div className="container" style={styles.container}>
        <div style={styles.glow}></div>
        <h1 style={styles.title}>
          Zero<span style={{ color: 'var(--accent-primary)' }}>Trace</span>
        </h1>
        <p style={styles.subtitle}>
          The Ultimate Data Destruction Tool. <br />
          Securely erase everything. Leave nos trace.
        </p>
        <div style={styles.badge}>NIST SP 800-88 Compliant</div>
        <button onClick={scrollToDownloads} style={styles.ctaButton}>
          Download Now
        </button>
      </div>
    </section>
  );
};

const styles = {
  heroSection: {
    height: '90vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    position: 'relative',
    overflow: 'hidden',
    background: 'radial-gradient(circle at center, #1a1a1a 0%, #050505 70%)',
  },
  container: {
    position: 'relative',
    zIndex: 2,
  },
  title: {
    fontSize: '5rem',
    fontWeight: '800',
    letterSpacing: '-2px',
    marginBottom: '20px',
    textTransform: 'uppercase',
  },
  subtitle: {
    fontSize: '1.5rem',
    color: 'var(--text-secondary)',
    marginBottom: '40px',
    maxWidth: '600px',
    marginLeft: 'auto',
    marginRight: 'auto',
  },
  ctaButton: {
    padding: '15px 40px',
    fontSize: '1.2rem',
    fontWeight: 'bold',
    backgroundColor: 'var(--accent-primary)',
    color: '#000',
    borderRadius: '4px',
    transition: 'transform 0.2s, box-shadow 0.2s',
    boxShadow: '0 0 20px rgba(0, 255, 157, 0.4)',
  },
  badge: {
    display: 'inline-block',
    padding: '8px 16px',
    border: '1px solid var(--accent-secondary)',
    color: 'var(--accent-secondary)',
    borderRadius: '20px',
    marginBottom: '30px',
    fontSize: '0.9rem',
    letterSpacing: '1px',
    textTransform: 'uppercase',
  },
  glow: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '600px',
    height: '600px',
    background: 'radial-gradient(circle, rgba(0,255,157,0.1) 0%, rgba(0,0,0,0) 70%)',
    zIndex: -1,
    pointerEvents: 'none',
  }
};

export default Hero;
