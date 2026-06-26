import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';

const Checkout = () => {
  const { cart, getCartTotal, clearCart } = useCart();
  const location = useLocation();
  const navigate = useLocation();

  // Retrieve discount passed from Cart page
  const discount = location.state?.discount || 0;

  // Checkout States: 'form', 'processing', 'success'
  const [checkoutState, setCheckoutState] = useState('form');
  const [processingMsg, setProcessingMsg] = useState('');
  const [formInputs, setFormInputs] = useState({
    name: '',
    email: '',
    cardNum: '4111 2222 3333 4444', // prefilled for easy testing
    cardExp: '12/29',
    cardCvv: '123'
  });
  const [generatedKeys, setGeneratedKeys] = useState([]);
  const [copiedKeyIndex, setCopiedKeyIndex] = useState(null);

  const subtotal = getCartTotal();
  const discountAmount = subtotal * discount;
  const taxRate = 0.10;
  const tax = (subtotal - discountAmount) * taxRate;
  const total = subtotal - discountAmount + tax;

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormInputs(prev => ({ ...prev, [name]: value }));
  };

  const generateLicenseKey = (planId) => {
    const segments = [];
    const prefix = planId.includes('enterprise') ? 'ZT-ENT' : 'ZT-PRO';
    segments.push(prefix);

    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    for (let s = 0; s < 3; s++) {
      let segment = '';
      for (let i = 0; i < 4; i++) {
        segment += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      segments.push(segment);
    }
    return segments.join('-');
  };

  const handlePay = (e) => {
    e.preventDefault();
    if (!formInputs.name || !formInputs.email) {
      alert('Please enter your name and email address.');
      return;
    }

    setCheckoutState('processing');
    setProcessingMsg('Verifying billing credentials...');

    // Simulate payment stages
    setTimeout(() => {
      setProcessingMsg('Contacting secure gateway...');
      setTimeout(() => {
        setProcessingMsg('Confirming payment authorization...');
        setTimeout(() => {
          setProcessingMsg('Generating license keys...');
          setTimeout(() => {
            // Generate keys based on items in the cart
            const keys = [];
            cart.forEach(item => {
              for (let q = 0; q < item.quantity; q++) {
                keys.push({
                  name: item.name,
                  key: generateLicenseKey(item.planId)
                });
              }
            });
            setGeneratedKeys(keys);
            setCheckoutState('success');
            clearCart(); // Empty the cart on successful checkout
          }, 1000);
        }, 1000);
      }, 1000);
    }, 1000);
  };

  const copyToClipboard = (keyText, index) => {
    navigator.clipboard.writeText(keyText);
    setCopiedKeyIndex(index);
    setTimeout(() => setCopiedKeyIndex(null), 2000);
  };

  const styles = {
    page: {
      minHeight: '100vh',
      padding: '120px 0 80px',
      background: 'var(--bg-color)',
      color: 'var(--text-primary)',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: '800',
      marginBottom: '10px',
      background: 'linear-gradient(45deg, #fff, #a0a0a0)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    subtitle: {
      fontSize: '1.05rem',
      color: 'var(--text-secondary)',
      marginBottom: '40px',
    },
    layout: {
      display: 'flex',
      gap: '40px',
      flexWrap: 'wrap',
    },
    formArea: {
      flex: '2',
      minWidth: '450px',
    },
    summaryArea: {
      flex: '1',
      minWidth: '320px',
    },
    card: {
      background: 'var(--card-bg)',
      border: '1px solid #222',
      borderRadius: '12px',
      padding: '30px',
      marginBottom: '20px',
    },
    formGroup: {
      marginBottom: '20px',
    },
    label: {
      display: 'block',
      fontSize: '0.85rem',
      fontWeight: '600',
      color: 'var(--text-secondary)',
      marginBottom: '8px',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    input: {
      width: '100%',
      padding: '12px 15px',
      background: '#151515',
      border: '1px solid #2d2d2d',
      borderRadius: '6px',
      color: '#fff',
      fontSize: '0.95rem',
      outline: 'none',
      boxSizing: 'border-box',
    },
    row: {
      display: 'flex',
      gap: '20px',
    },
    payBtn: {
      width: '100%',
      padding: '15px',
      background: 'var(--accent-primary)',
      color: '#000',
      border: 'none',
      borderRadius: '8px',
      fontWeight: '700',
      fontSize: '1.05rem',
      cursor: 'pointer',
      transition: 'all 0.2s',
      boxShadow: '0 4px 15px rgba(0, 255, 157, 0.2)',
      marginTop: '10px',
    },
    securityBadge: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      color: 'var(--text-secondary)',
      fontSize: '0.85rem',
      marginTop: '20px',
    },
    // Processing styles
    spinnerOverlay: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 40px',
      textAlign: 'center',
      background: 'var(--card-bg)',
      border: '1px solid #222',
      borderRadius: '12px',
    },
    spinner: {
      width: '50px',
      height: '50px',
      border: '4px solid #1a1a1a',
      borderTop: '4px solid var(--accent-primary)',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite',
      marginBottom: '25px',
    },
    processingTitle: {
      fontSize: '1.4rem',
      color: '#fff',
      fontWeight: 'bold',
      marginBottom: '10px',
    },
    processingSub: {
      color: 'var(--text-secondary)',
    },
    // Success view styles
    successHeader: {
      textAlign: 'center',
      paddingBottom: '30px',
      borderBottom: '1px solid #222',
      marginBottom: '30px',
    },
    successCheck: {
      fontSize: '4rem',
      marginBottom: '15px',
      display: 'block',
    },
    successTitle: {
      fontSize: '2rem',
      fontWeight: '800',
      color: 'var(--accent-primary)',
      textShadow: '0 0 10px rgba(0,255,157,0.2)',
    },
    licenseKeyCard: {
      background: '#151515',
      border: '1px solid #2d2d2d',
      borderRadius: '8px',
      padding: '20px',
      marginBottom: '15px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    keyText: {
      fontFamily: 'monospace',
      fontSize: '1.2rem',
      fontWeight: 'bold',
      color: 'var(--accent-primary)',
      letterSpacing: '1px',
    },
    copyBtn: {
      padding: '8px 16px',
      background: '#333',
      color: '#fff',
      border: 'none',
      borderRadius: '4px',
      fontSize: '0.8rem',
      fontWeight: '600',
      cursor: 'pointer',
      transition: 'background 0.2s',
    },
    // Order summary list
    summaryList: {
      listStyle: 'none',
      padding: 0,
      margin: '0 0 20px 0',
    },
    summaryItem: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '0.9rem',
      color: '#ccc',
      paddingBottom: '10px',
      marginBottom: '10px',
      borderBottom: '1px solid #1a1a1a',
    },
    summaryTitleRow: {
      fontSize: '1.25rem',
      fontWeight: '700',
      color: '#fff',
      borderBottom: '1px solid #2d2d2d',
      paddingBottom: '12px',
      marginBottom: '20px',
    }
  };

  return (
    <div style={styles.page}>
      
      {/* Dynamic Keyframe style for Spinner */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>

      <div className="container">
        
        {/* State 1: Form Filling */}
        {checkoutState === 'form' && (
          <>
            <h1 style={styles.title}>Secure Checkout</h1>
            <p style={styles.subtitle}>Enter your billing credentials to complete your license transaction.</p>

            {cart.length === 0 ? (
              <div style={styles.spinnerOverlay}>
                <h3>No Items in Checkout</h3>
                <p style={{color: 'var(--text-secondary)', margin: '15px 0 30px'}}>Please return to your cart or view pricing plans to checkout.</p>
                <Link to="/" style={{
                  padding: '12px 30px',
                  background: 'var(--accent-primary)',
                  color: '#000',
                  borderRadius: '6px',
                  fontWeight: '700',
                  textDecoration: 'none'
                }}>Go Home</Link>
              </div>
            ) : (
              <div style={styles.layout}>
                
                {/* Billing and Card Form */}
                <div style={styles.formArea}>
                  <form onSubmit={handlePay} style={styles.card}>
                    <h3 style={{...styles.summaryTitleRow, borderBottom: 'none', marginBottom: '10px', paddingBottom: '0'}}>
                      Billing Details
                    </h3>
                    
                    <div style={styles.formGroup}>
                      <label style={styles.label}>Full Name</label>
                      <input 
                        type="text" 
                        name="name" 
                        placeholder="John Doe" 
                        required 
                        value={formInputs.name}
                        onChange={handleInputChange}
                        style={styles.input} 
                      />
                    </div>
                    
                    <div style={styles.formGroup}>
                      <label style={styles.label}>Email Address</label>
                      <input 
                        type="email" 
                        name="email" 
                        placeholder="johndoe@security.com" 
                        required 
                        value={formInputs.email}
                        onChange={handleInputChange}
                        style={styles.input} 
                      />
                    </div>

                    <h3 style={{...styles.summaryTitleRow, borderBottom: 'none', marginBottom: '10px', paddingBottom: '0', marginTop: '30px'}}>
                      Payment Details
                    </h3>

                    <div style={styles.formGroup}>
                      <label style={styles.label}>Card Number</label>
                      <input 
                        type="text" 
                        name="cardNum" 
                        placeholder="4111 2222 3333 4444" 
                        required 
                        value={formInputs.cardNum}
                        onChange={handleInputChange}
                        style={styles.input} 
                      />
                    </div>

                    <div style={styles.row}>
                      <div style={{...styles.formGroup, flex: 1}}>
                        <label style={styles.label}>Expiration Date</label>
                        <input 
                          type="text" 
                          name="cardExp" 
                          placeholder="MM/YY" 
                          required 
                          value={formInputs.cardExp}
                          onChange={handleInputChange}
                          style={styles.input} 
                        />
                      </div>
                      <div style={{...styles.formGroup, flex: 1}}>
                        <label style={styles.label}>CVV</label>
                        <input 
                          type="text" 
                          name="cardCvv" 
                          placeholder="123" 
                          required 
                          value={formInputs.cardCvv}
                          onChange={handleInputChange}
                          style={styles.input} 
                        />
                      </div>
                    </div>

                    <button type="submit" style={styles.payBtn}>
                      Pay Securely (${total.toFixed(2)})
                    </button>

                    <div style={styles.securityBadge}>
                      <span>🔒</span> 256-Bit SSL Encrypted Connection
                    </div>
                  </form>
                </div>

                {/* Checkout Summary panel */}
                <div style={styles.summaryArea}>
                  <div style={styles.card}>
                    <h3 style={styles.summaryTitleRow}>Order Summary</h3>
                    
                    <ul style={styles.summaryList}>
                      {cart.map((item) => (
                        <li key={item.id} style={styles.summaryItem}>
                          <div>
                            <div style={{fontWeight: '700', color: '#fff'}}>{item.name}</div>
                            <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)'}}>Qty: {item.quantity}</div>
                          </div>
                          <span style={{fontFamily: 'monospace'}}>${(item.price * item.quantity).toFixed(2)}</span>
                        </li>
                      ))}
                    </ul>

                    <div style={{...styles.summaryRow, fontSize: '0.9rem'}}>
                      <span>Subtotal</span>
                      <span style={{fontFamily: 'monospace'}}>${subtotal.toFixed(2)}</span>
                    </div>

                    {discount > 0 && (
                      <div style={{...styles.summaryRow, fontSize: '0.9rem', color: 'var(--accent-primary)'}}>
                        <span>Discount (20%)</span>
                        <span style={{fontFamily: 'monospace'}}>-${discountAmount.toFixed(2)}</span>
                      </div>
                    )}

                    <div style={{...styles.summaryRow, fontSize: '0.9rem', marginBottom: '20px'}}>
                      <span>VAT / Taxes (10%)</span>
                      <span style={{fontFamily: 'monospace'}}>${tax.toFixed(2)}</span>
                    </div>

                    <div style={{...styles.totalRow, marginTop: '0', paddingTop: '20px', marginBottom: '0'}}>
                      <span>Total Billed</span>
                      <span style={{color: 'var(--accent-primary)'}}>${total.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

              </div>
            )}
          </>
        )}

        {/* State 2: Simulated Processing Spinner */}
        {checkoutState === 'processing' && (
          <div style={{maxWidth: '550px', margin: '0 auto'}}>
            <div style={styles.spinnerOverlay}>
              <div style={styles.spinner}></div>
              <h2 style={styles.processingTitle}>Processing Transaction</h2>
              <p style={styles.processingSub}>{processingMsg}</p>
            </div>
          </div>
        )}

        {/* State 3: Success Screen with Keys */}
        {checkoutState === 'success' && (
          <div style={{maxWidth: '680px', margin: '0 auto'}}>
            <div style={styles.card}>
              <div style={styles.successHeader}>
                <span style={styles.successCheck}>🛡️</span>
                <h1 style={styles.successTitle}>Order Completed Successfully!</h1>
                <p style={{color: 'var(--text-secondary)', marginTop: '8px'}}>Your order receipt has been sent to <strong>{formInputs.email}</strong>.</p>
              </div>

              <div style={{marginBottom: '35px'}}>
                <h3 style={{...styles.summaryTitleRow, borderBottom: 'none', marginBottom: '10px', paddingBottom: '0'}}>
                  Your Activated License Keys
                </h3>
                <p style={{color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px', lineHeight: '1.4'}}>
                  Copy these keys and enter them into the **ZeroTrace Desktop App** settings menu (Admin -> Activate Key) to unlock professional features.
                </p>

                {generatedKeys.map((item, index) => (
                  <div key={index}>
                    <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 'bold', marginBottom: '6px'}}>
                      License {index + 1}: {item.name}
                    </div>
                    <div style={styles.licenseKeyCard}>
                      <span style={styles.keyText}>{item.key}</span>
                      <button 
                        onClick={() => copyToClipboard(item.key, index)}
                        style={{
                          ...styles.copyBtn,
                          backgroundColor: copiedKeyIndex === index ? 'var(--accent-primary)' : '#333',
                          color: copiedKeyIndex === index ? '#000' : '#fff'
                        }}
                      >
                        {copiedKeyIndex === index ? 'Copied! ✓' : 'Copy'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{textAlign: 'center', display: 'flex', gap: '20px', justifyContent: 'center'}}>
                <a href="/#downloads" style={{
                  padding: '12px 30px',
                  background: 'var(--accent-primary)',
                  color: '#000',
                  borderRadius: '6px',
                  fontWeight: '700',
                  textDecoration: 'none',
                  boxShadow: '0 4px 15px rgba(0, 255, 157, 0.2)'
                }}>
                  Download Desktop Tool
                </a>
                <Link to="/" style={{
                  padding: '12px 30px',
                  background: '#222',
                  color: '#fff',
                  border: '1px solid #333',
                  borderRadius: '6px',
                  fontWeight: '700',
                  textDecoration: 'none'
                }}>
                  Return to Home
                </Link>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default Checkout;
