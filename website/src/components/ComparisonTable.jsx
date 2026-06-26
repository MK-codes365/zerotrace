import React from 'react';

const ComparisonTable = () => {
  return (
    <section style={styles.section}>
      <div className="container">
        <h2 style={styles.header}>Enterprise Ready</h2>
        <div style={styles.tableWrapper}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Feature</th>
                <th style={styles.th}>Community</th>
                <th style={{...styles.th, color: 'var(--accent-primary)'}}>Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {[ 
                ["Data Sanitization (NIST)", "✅", "✅"],
                ["PDF Verification Certificates", "✅", "✅"],
                ["Unlimited Drives", "✅", "✅"],
                ["Centralized Management Console", "❌", "✅"],
                ["Active Directory / SSO Integration", "❌", "✅"],
                ["Automated Network Scanning", "❌", "✅"],
                ["24/7 Dedicated Support", "❌", "✅"],
                ["Custom Audit Logs", "❌", "✅"],
              ].map((row, i) => (
                <tr key={i} style={styles.tr}>
                  <td style={styles.tdFeature}>{row[0]}</td>
                  <td style={styles.td}>{row[1]}</td>
                  <td style={styles.td}>{row[2]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={styles.cta}>
          <p style={styles.ctaText}>Need to wipe 100+ devices?</p>
          <button style={styles.button}>Contact Sales</button>
        </div>
      </div>
    </section>
  );
};

const styles = {
  section: {
    padding: '100px 0',
    backgroundColor: '#0a0a0a', // Slightly darker bg for contrast
  },
  header: {
    textAlign: 'center',
    fontSize: '2.5rem',
    marginBottom: '60px',
  },
  tableWrapper: {
    maxWidth: '900px',
    margin: '0 auto',
    overflowX: 'auto', // For mobile responsiveness
    background: 'var(--card-bg)',
    borderRadius: '16px',
    padding: '20px',
    border: '1px solid #333',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    minWidth: '600px', // Force scroll on very small screens
  },
  th: {
    padding: '20px',
    textAlign: 'left',
    fontSize: '1.2rem',
    borderBottom: '1px solid #333',
    color: 'var(--text-primary)',
  },
  tr: {
    borderBottom: '1px solid #1a1a1a',
  },
  tdFeature: {
    padding: '20px',
    color: 'var(--text-secondary)',
    fontWeight: '500',
  },
  td: {
    padding: '20px',
    textAlign: 'center',
    fontSize: '1.2rem',
  },
  cta: {
    textAlign: 'center',
    marginTop: '60px',
  },
  ctaText: {
    fontSize: '1.5rem',
    marginBottom: '20px',
    color: 'var(--text-primary)',
  },
  button: {
    padding: '15px 40px',
    fontSize: '1.1rem',
    fontWeight: '600',
    backgroundColor: 'var(--text-primary)',
    color: '#000',
    borderRadius: '50px',
    border: 'none',
    cursor: 'pointer',
    transition: '0.3s',
  }
};

export default ComparisonTable;
