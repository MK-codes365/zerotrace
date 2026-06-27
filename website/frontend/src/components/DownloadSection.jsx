import React from 'react';

const DownloadSection = () => {
  return (
    <section id="downloads" style={styles.section}>
      <div className="container">
        <h2 style={styles.header}>Get ZeroTrace</h2>
        <p style={styles.subtext}>Select your platform to start wiping data securely.</p>
        
        <div style={styles.grid}>
          {/* Windows */}
          <div style={{...styles.card, borderColor: 'var(--accent-secondary)'}}>
            <h3 style={styles.osTitle}>Windows</h3>
            <p style={styles.version}>v1.0.0 | x64</p>
            <button style={{...styles.button, backgroundColor: 'var(--accent-secondary)'}}>
              Download .EXE
            </button>
          </div>

          {/* Linux */}
          <div style={styles.card}>
            <h3 style={styles.osTitle}>Linux</h3>
            <p style={styles.version}>v1.0.0 | Deb/RPM</p>
            <button style={styles.button}>
              Download .Run
            </button>
          </div>

          {/* Android */}
          <div style={styles.card}>
            <h3 style={styles.osTitle}>Android</h3>
            <p style={styles.version}>v1.0.0 | APK</p>
            <button style={styles.button}>
              Download .APK
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

const styles = {
  section: {
    padding: '100px 0',
    background: 'linear-gradient(to bottom, var(--bg-color), #0f0f0f)',
  },
  header: {
    textAlign: 'center',
    fontSize: '3rem',
    marginBottom: '10px',
  },
  subtext: {
    textAlign: 'center',
    color: 'var(--text-secondary)',
    marginBottom: '60px',
  },
  grid: {
    display: 'flex',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: '40px',
  },
  card: {
    background: 'var(--card-bg)',
    padding: '40px',
    borderRadius: '16px',
    width: '300px',
    textAlign: 'center',
    border: '1px solid #333',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  osTitle: {
    fontSize: '1.8rem',
    marginBottom: '10px',
  },
  version: {
    color: 'var(--text-secondary)',
    marginBottom: '30px',
  },
  button: {
    padding: '12px 30px',
    fontSize: '1rem',
    fontWeight: '600',
    backgroundColor: '#333',
    color: '#fff',
    borderRadius: '8px',
    width: '100%',
    transition: '0.3s',
  }
};

export default DownloadSection;
