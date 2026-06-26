import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCart } from '../context/CartContext';

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const { getCartCount } = useCart();
  const cartCount = getCartCount();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav style={{ ...styles.nav, ...(scrolled ? styles.navScrolled : {}) }}>
      <div className="container" style={styles.container}>
        <Link to="/" style={styles.logo}>
          Zero<span style={{ color: 'var(--accent-primary)' }}>Trace</span>
        </Link>
        <div style={styles.links}>
          <Link to="/" style={location.pathname === '/' ? styles.activeLink : styles.link}>Home</Link>
          <Link to="/about" style={location.pathname === '/about' ? styles.activeLink : styles.link}>About</Link>
          <a href="/#downloads" style={styles.link}>Download</a>
          <Link to="/cart" style={location.pathname === '/cart' ? styles.activeCartLink : styles.cartLink}>
            🛒
            {cartCount > 0 && (
              <span style={styles.cartBadge}>{cartCount}</span>
            )}
          </Link>
        </div>
      </div>
    </nav>
  );
};

const styles = {
  nav: {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    zIndex: 1000,
    padding: '20px 0',
    transition: 'all 0.3s ease',
    background: 'transparent',
  },
  navScrolled: {
    padding: '15px 0',
    background: 'rgba(5, 5, 5, 0.8)',
    backdropFilter: 'blur(10px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  container: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    textDecoration: 'none',
    color: '#fff',
    letterSpacing: '-1px',
  },
  links: {
    display: 'flex',
    gap: '30px',
    alignItems: 'center',
  },
  link: {
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    fontSize: '1rem',
    fontWeight: '500',
    transition: 'color 0.3s',
  },
  activeLink: {
    color: '#fff',
    textDecoration: 'none',
    fontSize: '1rem',
    fontWeight: '500',
  },
  cartLink: {
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    fontSize: '1.1rem',
    display: 'flex',
    alignItems: 'center',
    position: 'relative',
    transition: 'color 0.3s',
    cursor: 'pointer',
  },
  activeCartLink: {
    color: '#fff',
    textDecoration: 'none',
    fontSize: '1.1rem',
    display: 'flex',
    alignItems: 'center',
    position: 'relative',
    cursor: 'pointer',
  },
  cartBadge: {
    position: 'absolute',
    top: '-8px',
    right: '-10px',
    background: 'var(--accent-primary)',
    color: '#000',
    borderRadius: '50%',
    width: '18px',
    height: '18px',
    fontSize: '0.7rem',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 0 5px rgba(0, 255, 157, 0.5)',
  }
};

export default Navbar;
