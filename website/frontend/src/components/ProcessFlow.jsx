import React from 'react';

const ProcessFlow = () => {
  const steps = [
    {
      num: "01",
      title: "Discovery",
      desc: "Automatically scan specific drives, partitions, or external media for sensitive data.",
      color: "#00ff9d"
    },
    {
      num: "02",
      title: "Sanitization",
      desc: "Apply military-grade algorithms (NIST/DoD) to irreversibly overwrite data blocks.",
      color: "#00b8ff"
    },
    {
      num: "03",
      title: "Verification",
      desc: "Generate a cryptographically signed pdf certificate proving 100% data destruction.",
      color: "#bd00ff"
    }
  ];

  return (
    <section style={styles.section}>
      <div className="container">
        <h2 style={styles.header}>How It Works</h2>
        <div style={styles.flowContainer}>
          {steps.map((step, index) => (
            <div key={index} style={styles.stepCard}>
              <div style={{...styles.number, color: step.color}}>{step.num}</div>
              <h3 style={styles.title}>{step.title}</h3>
              <p style={styles.desc}>{step.desc}</p>
              {index < steps.length - 1 && <div style={styles.connector}></div>}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const styles = {
  section: {
    padding: '100px 0',
    backgroundColor: 'var(--bg-color)',
  },
  header: {
    textAlign: 'center',
    fontSize: '2.5rem',
    marginBottom: '80px',
  },
  flowContainer: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: '40px',
    flexWrap: 'wrap',
  },
  stepCard: {
    flex: '1',
    minWidth: '300px',
    background: 'var(--card-bg)',
    padding: '40px',
    borderRadius: '16px',
    border: '1px solid #222',
    position: 'relative',
  },
  number: {
    fontSize: '3rem',
    fontWeight: '800',
    marginBottom: '20px',
    opacity: 0.8,
  },
  title: {
    fontSize: '1.5rem',
    marginBottom: '15px',
    color: 'var(--text-primary)',
  },
  desc: {
    color: 'var(--text-secondary)',
    lineHeight: '1.6',
  },
  connector: {
    // Conceptual connector, purely visual via CSS if needed, omitting complicated absolute positioning for now to ensure mobile responsiveness safety
  }
};

export default ProcessFlow;
