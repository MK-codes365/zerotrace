import React from 'react';

const Footer = () => {
  return (
    <footer style={styles.footer}>
      <div className="container">
        <p>&copy; {new Date().getFullYear()} ZeroTrace. Open Source & Secure.</p>
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
  }
};

export default Footer;
