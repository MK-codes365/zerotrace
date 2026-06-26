import React from 'react';

const StatsCounter = () => {
  return (
    <section style={styles.section}>
      <div className="container">
        <div style={styles.grid}>
          <div style={styles.item}>
            <div style={styles.number}>10M+</div>
            <div style={styles.label}>Files Wiped</div>
          </div>
          <div style={styles.item}>
            <div style={styles.number}>500TB</div>
            <div style={styles.label}>Data Secured</div>
          </div>
          <div style={styles.item}>
            <div style={styles.number}>100%</div>
            <div style={styles.label}>NIST Compliant</div>
          </div>
          <div style={styles.item}>
            <div style={styles.number}>50k+</div>
            <div style={styles.label}>Active Users</div>
          </div>
        </div>
      </div>
    </section>
  );
};

const styles = {
  section: {
    padding: '60px 0',
    background: 'linear-gradient(90deg, #111 0%, #050505 100%)',
    borderTop: '1px solid #222',
    borderBottom: '1px solid #222',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '30px',
    textAlign: 'center',
  },
  number: {
    fontSize: '3rem',
    fontWeight: '800',
    backgroundImage: 'linear-gradient(45deg, #fff, #666)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: '5px',
  },
  label: {
    color: 'var(--accent-primary)',
    fontSize: '1rem',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    fontWeight: '600',
  }
};

export default StatsCounter;
