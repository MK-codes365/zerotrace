import React from 'react';

const TrustedBy = () => {
  const companies = [
    "CYBERDYNE SYSTEMS", "MASSIVE DYNAMIC", "WAYNE ENTERPRISES", "UMBRELLA CORP", "STARK INDUSTRIES"
  ];

  return (
    <section style={styles.section}>
      <div className="container">
        <p style={styles.label}>TRUSTED BY SECURITY TEAMS AT</p>
        <div style={styles.logoGrid}>
          {companies.map((company, index) => (
            <div key={index} style={styles.logoItem}>
              {company}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const styles = {
  section: {
    padding: '40px 0',
    background: '#0a0a0a',
    borderBottom: '1px solid #222',
  },
  label: {
    textAlign: 'center',
    color: '#666',
    fontSize: '0.8rem',
    letterSpacing: '2px',
    marginBottom: '30px',
    fontWeight: '600',
  },
  logoGrid: {
    display: 'flex',
    justifyContent: 'center',
    gap: '60px',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  logoItem: {
    color: '#444',
    fontSize: '1.2rem',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    userSelect: 'none',
  }
};

export default TrustedBy;
