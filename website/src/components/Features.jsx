import React from 'react';

const Features = () => {
  const features = [
    {
      title: "Secure Erase",
      desc: "Implements DoD 5220.22-M and NIST standards to overwrite data multiple times.",
      icon: "🛡️"
    },
    {
      title: "Proof of Destruction",
      desc: "Generates digitally signed PDF/JSON certificates to verify the wipe.",
      icon: "📜"
    },
    {
      title: "Cross Platform",
      desc: "Unified experience across Windows, Linux, and Android devices.",
      icon: "🌐"
    }
  ];

  return (
    <section style={styles.section}>
      <div className="container">
        <h2 style={styles.header}>Why ZeroTrace?</h2>
        <div style={styles.grid}>
          {features.map((f, i) => (
            <div key={i} style={styles.card}>
              <div style={styles.icon}>{f.icon}</div>
              <h3 style={styles.cardTitle}>{f.title}</h3>
              <p style={styles.cardDesc}>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const styles = {
  section: {
    padding: '80px 0',
    backgroundColor: 'var(--bg-color)',
  },
  header: {
    textAlign: 'center',
    fontSize: '2.5rem',
    marginBottom: '60px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '30px',
  },
  card: {
    backgroundColor: 'var(--card-bg)',
    padding: '40px',
    borderRadius: '12px',
    border: '1px solid #222',
    transition: 'transform 0.3s',
  },
  icon: {
    fontSize: '3rem',
    marginBottom: '20px',
  },
  cardTitle: {
    fontSize: '1.5rem',
    marginBottom: '15px',
    color: 'var(--text-primary)',
  },
  cardDesc: {
    color: 'var(--text-secondary)',
  }
};

export default Features;
