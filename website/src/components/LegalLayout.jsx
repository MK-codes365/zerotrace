import React from 'react';
import { Link } from 'react-router-dom';

const LegalLayout = ({ title, children }) => {
  return (
    <div style={styles.page}>
      <div className="container" style={styles.container}>
        <Link to="/" style={styles.backLink}>
          ← Back to Home
        </Link>
        <div style={styles.card}>
          <h1 style={styles.title}>{title}</h1>
          <div style={styles.content}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  page: {
    minHeight: '100vh',
    padding: '120px 0 60px', // Top padding to clear fixed header if any, or just spacing
    background: 'var(--bg-color)',
  },
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '0 20px',
  },
  backLink: {
    display: 'inline-block',
    marginBottom: '30px',
    color: 'var(--text-secondary)',
    fontSize: '0.9rem',
    fontWeight: '500',
    textDecoration: 'none',
  },
  card: {
    background: 'var(--card-bg)',
    borderRadius: '16px',
    padding: '40px',
    border: '1px solid #222',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
  },
  title: {
    fontSize: '2.5rem',
    marginBottom: '30px',
    background: 'linear-gradient(45deg, #fff, #a0a0a0)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  content: {
    color: 'var(--text-secondary)',
    lineHeight: '1.8',
    fontSize: '1.05rem',
  }
};

export default LegalLayout;
