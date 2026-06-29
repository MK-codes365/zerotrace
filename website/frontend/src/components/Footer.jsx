import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer style={styles.footer}>
      <div className="container">
        <p>&copy; {new Date().getFullYear()} ZeroTrace. Open Source & Secure.</p>
        <div style={styles.linksContainer}>
          <Link to="/terms" style={styles.link} onMouseOver={(e) => e.target.style.color = '#fff'} onMouseOut={(e) => e.target.style.color = 'var(--text-secondary)'}>Terms & Conditions</Link>
          <span style={styles.separator}>|</span>
          <Link to="/privacy" style={styles.link} onMouseOver={(e) => e.target.style.color = '#fff'} onMouseOut={(e) => e.target.style.color = 'var(--text-secondary)'}>Privacy Policy</Link>
          <span style={styles.separator}>|</span>
          <Link to="/contact" style={styles.link} onMouseOver={(e) => e.target.style.color = '#fff'} onMouseOut={(e) => e.target.style.color = 'var(--text-secondary)'}>Contact Support</Link>
        </div>
      </div>
    </footer>
  );
};

const styles = {
  footer: {
    padding: '40px 0',
    textAlign: 'center',
    borderTop: '1px solid #222',
    color: 'var(--text-secondary)',
    fontSize: '0.9rem',
  },
  linksContainer: {
    marginTop: '15px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '15px',
  },
  link: {
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    fontSize: '0.85rem',
    cursor: 'pointer',
    transition: 'color 0.2s ease',
  },
  separator: {
    color: '#333',
  }
};

export default Footer;
