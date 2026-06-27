import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';

const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

const Checkout = () => {
  const { cart, getCartTotal, clearCart } = useCart();
  const location = useLocation();

  // Retrieve discount passed from Cart page
  const discount = location.state?.discount || 0;

  // Checkout States: 'form', 'processing', 'success'
  const [checkoutState, setCheckoutState] = useState('form');
  const [processingMsg, setProcessingMsg] = useState('');
  const [showMockModal, setShowMockModal] = useState(false);
  const [activeMockTab, setActiveMockTab] = useState('qr'); // 'qr' or 'methods'
  const [formInputs, setFormInputs] = useState({
    name: '',
    email: ''
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

  const handlePay = async (e) => {
    e.preventDefault();
    if (!formInputs.name || !formInputs.email) {
      alert('Please enter your name and email address.');
      return;
    }

    const key = import.meta.env.VITE_RAZORPAY_KEY_ID;
    const isDemoMode = !key || key.trim() === '' || key.startsWith('rzp_test_placeholder') || key === 'rzp_test_dummykey123' || key === 'rzp_test_4K6F6mH2tP9G9h';

    if (isDemoMode) {
      // Demo Mock Mode
      setCheckoutState('processing');
      setProcessingMsg('Initializing Demo Payment Gateway...');
      setTimeout(() => {
        setCheckoutState('form');
        setShowMockModal(true);
      }, 1000);
      return;
    }

    // Real Razorpay Mode
    setCheckoutState('processing');
    setProcessingMsg('Creating secure order...');

    let orderData;
    try {
      const amountInPaise = Math.round(total * 100);
      const res = await fetch('http://localhost:5000/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amountInPaise, currency: 'INR' })
      });

      if (!res.ok) {
        throw new Error('Backend failed to create order');
      }

      orderData = await res.json();
    } catch (err) {
      console.error('Order creation error:', err);
      alert('Failed to initialize transaction with backend.');
      setCheckoutState('form');
      return;
    }

    setProcessingMsg('Loading Razorpay Secure Gateway...');

    const isLoaded = await loadRazorpayScript();
    if (!isLoaded) {
      alert('Failed to load Razorpay SDK. Please check your network connection.');
      setCheckoutState('form');
      return;
    }

    setProcessingMsg('Opening payment window...');

    const options = {
      key: key,
      amount: orderData.amount,
      currency: orderData.currency,
      order_id: orderData.id,
      name: 'ZeroTrace',
      description: 'ZeroTrace Pro/Enterprise License Purchase',
      image: 'https://via.placeholder.com/128/00d9ff/000000?text=ZeroTrace',
      handler: async function (response) {
        setProcessingMsg('Verifying payment signature...');

        try {
          const verifyRes = await fetch('http://localhost:5000/api/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              cart: cart,
              email: formInputs.email
            })
          });

          if (!verifyRes.ok) {
            const errData = await verifyRes.json();
            throw new Error(errData.error || 'Signature verification failed');
          }

          const verifyData = await verifyRes.json();
          setGeneratedKeys(verifyData.keys);
          setCheckoutState('success');
          clearCart();
        } catch (err) {
          console.error('Signature verification error:', err);
          alert(`Verification failed: ${err.message}`);
          setCheckoutState('form');
        }
      },
      prefill: {
        name: formInputs.name,
        email: formInputs.email
      },
      theme: {
        color: '#00ff9d'
      },
      modal: {
        ondismiss: function () {
          setCheckoutState('form');
        }
      }
    };

    try {
      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response) {
        alert(`Payment failed: ${response.error.description}`);
        setCheckoutState('form');
      });
      rzp.open();
    } catch (err) {
      console.error('Razorpay initialization error:', err);
      alert('Failed to open Razorpay payment window.');
      setCheckoutState('form');
    }
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
    },
    // Mock Modal Styles
    modalOverlay: {
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0,0,0,0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      backdropFilter: 'blur(8px)',
    },
    modalContainer: {
      background: '#121218',
      border: '1px solid var(--accent-primary)',
      borderRadius: '16px',
      width: '90%',
      maxWidth: '440px',
      padding: '30px',
      position: 'relative',
      boxShadow: '0 0 30px rgba(0, 255, 157, 0.25)',
      color: '#fff',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    modalCloseBtn: {
      position: 'absolute',
      top: '15px',
      right: '20px',
      background: 'none',
      border: 'none',
      color: '#888',
      fontSize: '1.2rem',
      cursor: 'pointer',
      padding: '5px',
    },
    modalHeader: {
      display: 'flex',
      alignItems: 'center',
      gap: '15px',
      borderBottom: '1px solid #222',
      paddingBottom: '20px',
      marginBottom: '20px',
    },
    modalLogo: {
      width: '50px',
      height: '50px',
      borderRadius: '10px',
      background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
      color: '#000',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: '800',
      fontSize: '1.3rem',
    },
    modalMerchantName: {
      fontSize: '1.2rem',
      fontWeight: '700',
      margin: 0,
    },
    modalDesc: {
      fontSize: '0.8rem',
      color: '#888',
      margin: '2px 0 0 0',
    },
    modalAmountContainer: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      background: '#1a1a24',
      padding: '15px 20px',
      borderRadius: '8px',
      marginBottom: '20px',
      border: '1px solid #2a2a3a',
    },
    modalAmountLabel: {
      fontSize: '0.9rem',
      color: '#aaa',
    },
    modalAmountValue: {
      fontSize: '1.4rem',
      fontWeight: '800',
      color: 'var(--accent-primary)',
    },
    modalInfoBox: {
      fontSize: '0.85rem',
      background: '#15151b',
      padding: '12px 15px',
      borderRadius: '6px',
      marginBottom: '20px',
      lineHeight: '1.4',
      border: '1px solid #222',
    },
    modalMethods: {
      display: 'flex',
      flexDirection: 'column',
      gap: '10px',
      marginBottom: '25px',
    },
    modalMethodRow: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '0.85rem',
      padding: '8px 0',
      borderBottom: '1px dashed #222',
      color: '#ccc',
    },
    modalMethodCheck: {
      color: 'var(--accent-primary)',
      fontWeight: 'bold',
    },
    modalActions: {
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
    },
    modalSuccessBtn: {
      width: '100%',
      padding: '14px',
      background: 'var(--accent-primary)',
      color: '#000',
      border: 'none',
      borderRadius: '8px',
      fontWeight: '700',
      fontSize: '1rem',
      cursor: 'pointer',
      transition: 'opacity 0.2s',
      boxShadow: '0 4px 12px rgba(0, 255, 157, 0.2)',
    },
    modalFailBtn: {
      width: '100%',
      padding: '14px',
      background: 'transparent',
      color: '#ff4d4d',
      border: '1px solid #ff4d4d',
      borderRadius: '8px',
      fontWeight: '600',
      fontSize: '1rem',
      cursor: 'pointer',
      transition: 'background 0.2s',
    },
    modalFooter: {
      textAlign: 'center',
      fontSize: '0.75rem',
      color: '#555',
      marginTop: '20px',
    }
  };

  return (
    <div style={styles.page}>
      
      {/* Dynamic Keyframe style for Spinner & Pulse */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0% { opacity: 0.3; transform: scale(0.95); }
          50% { opacity: 1; transform: scale(1.05); }
          100% { opacity: 0.3; transform: scale(0.95); }
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
                      Payment Method
                    </h3>

                    <div style={{
                      background: '#151515',
                      border: '1px solid #2d2d2d',
                      borderRadius: '8px',
                      padding: '20px',
                      marginBottom: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '15px',
                    }}>
                      <div style={{fontSize: '2rem'}}>💳</div>
                      <div>
                        <div style={{fontWeight: '700', color: '#fff'}}>Razorpay Secure Checkout</div>
                        <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px'}}>
                          Supports Credit/Debit Cards, UPI, Netbanking, and Wallets.
                        </div>
                      </div>
                    </div>

                    {!import.meta.env.VITE_RAZORPAY_KEY_ID && (
                      <div style={{
                        background: 'rgba(0, 217, 255, 0.08)',
                        border: '1px dashed rgba(0, 217, 255, 0.3)',
                        borderRadius: '8px',
                        padding: '12px 15px',
                        fontSize: '0.85rem',
                        color: '#00d9ff',
                        marginBottom: '20px',
                        lineHeight: '1.4'
                      }}>
                        ℹ️ <strong>Demo Mode:</strong> No Razorpay Key ID was detected in environment variables. Checkout will launch using a default test key.
                      </div>
                    )}

                    <button type="submit" style={styles.payBtn}>
                      Pay Securely (₹${total.toFixed(2)})
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
                          <span style={{fontFamily: 'monospace'}}>₹{(item.price * item.quantity).toFixed(2)}</span>
                        </li>
                      ))}
                    </ul>

                    <div style={{...styles.summaryRow, fontSize: '0.9rem'}}>
                      <span>Subtotal</span>
                      <span style={{fontFamily: 'monospace'}}>₹{subtotal.toFixed(2)}</span>
                    </div>

                    {discount > 0 && (
                      <div style={{...styles.summaryRow, fontSize: '0.9rem', color: 'var(--accent-primary)'}}>
                        <span>Discount (20%)</span>
                        <span style={{fontFamily: 'monospace'}}>-₹{discountAmount.toFixed(2)}</span>
                      </div>
                    )}

                    <div style={{...styles.summaryRow, fontSize: '0.9rem', marginBottom: '20px'}}>
                      <span>VAT / Taxes (10%)</span>
                      <span style={{fontFamily: 'monospace'}}>₹{tax.toFixed(2)}</span>
                    </div>

                    <div style={{...styles.totalRow, marginTop: '0', paddingTop: '20px', marginBottom: '0'}}>
                      <span>Total Billed</span>
                      <span style={{color: 'var(--accent-primary)'}}>₹{total.toFixed(2)}</span>
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
                  Copy these keys and enter them into the **ZeroTrace Desktop App** settings menu (Admin &rarr; Activate Key) to unlock professional features.
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

        {/* State 4: Mock Razorpay Modal (Demo Mode) */}
        {showMockModal && (
          <div style={styles.modalOverlay}>
            <div style={styles.modalContainer}>
              <button 
                onClick={() => setShowMockModal(false)}
                style={styles.modalCloseBtn}
              >
                ✕
              </button>

              <div style={styles.modalHeader}>
                <div style={styles.modalLogo}>ZT</div>
                <div>
                  <h3 style={styles.modalMerchantName}>ZeroTrace Checkout</h3>
                  <p style={styles.modalDesc}>Demo transaction simulation</p>
                </div>
              </div>

              {/* Tab Navigation */}
              <div style={{
                display: 'flex',
                borderBottom: '1px solid #222',
                marginBottom: '20px',
                gap: '15px'
              }}>
                <button
                  onClick={() => setActiveMockTab('qr')}
                  style={{
                    background: 'none',
                    border: 'none',
                    borderBottom: activeMockTab === 'qr' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                    color: activeMockTab === 'qr' ? 'var(--accent-primary)' : '#888',
                    padding: '8px 12px 12px 12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    transition: 'all 0.2s',
                    flex: 1
                  }}
                >
                  🔍 UPI QR Code
                </button>
                <button
                  onClick={() => setActiveMockTab('methods')}
                  style={{
                    background: 'none',
                    border: 'none',
                    borderBottom: activeMockTab === 'methods' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                    color: activeMockTab === 'methods' ? 'var(--accent-primary)' : '#888',
                    padding: '8px 12px 12px 12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    transition: 'all 0.2s',
                    flex: 1
                  }}
                >
                  💳 Other Methods
                </button>
              </div>

              <div style={styles.modalAmountContainer}>
                <span style={styles.modalAmountLabel}>Total Amount</span>
                <span style={styles.modalAmountValue}>₹{total.toFixed(2)}</span>
              </div>

              <div style={styles.modalInfoBox}>
                <p style={{margin: '0 0 5px 0'}}><strong>Customer Name:</strong> {formInputs.name}</p>
                <p style={{margin: 0}}><strong>Customer Email:</strong> {formInputs.email}</p>
              </div>

              {activeMockTab === 'qr' && (
                <div>
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: '#15151b',
                    border: '1px solid #222',
                    borderRadius: '8px',
                    padding: '20px',
                    marginBottom: '20px',
                    textAlign: 'center'
                  }}>
                    <div style={{
                      background: '#fff',
                      padding: '10px',
                      borderRadius: '8px',
                      marginBottom: '15px',
                      boxShadow: '0 0 15px rgba(0, 255, 157, 0.2)',
                      display: 'inline-block'
                    }}>
                      <img 
                        src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa=zerotrace@upi%26pn=ZeroTrace%20Technologies%26am=${total.toFixed(2)}%26cu=INR`} 
                        alt="Simulated UPI QR Code" 
                        style={{ display: 'block', width: '150px', height: '150px' }}
                      />
                    </div>
                    <div style={{fontSize: '0.9rem', fontWeight: 'bold', color: '#fff', marginBottom: '6px'}}>
                      Scan QR Code to Pay
                    </div>
                    <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: '1.4', maxWidth: '280px'}}>
                      Scan this QR code using any UPI app (GPay, PhonePe, Paytm, BHIM) to complete your transaction of <strong>₹{total.toFixed(2)}</strong>.
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontSize: '0.8rem',
                    color: 'var(--accent-primary)',
                    marginBottom: '20px',
                    fontWeight: '600'
                  }}>
                    <span style={{
                      width: '8px',
                      height: '8px',
                      background: 'var(--accent-primary)',
                      borderRadius: '50%',
                      display: 'inline-block',
                      animation: 'pulse 1.5s infinite'
                    }}></span>
                    <span>Waiting for scan verification...</span>
                  </div>

                  <div style={styles.modalActions}>
                    <button 
                      onClick={() => {
                        setShowMockModal(false);
                        setCheckoutState('processing');
                        setProcessingMsg('Verifying QR Code payment...');
                        setTimeout(() => {
                          setProcessingMsg('Generating license keys...');
                          setTimeout(() => {
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
                            clearCart();
                          }, 1000);
                        }, 1000);
                      }}
                      style={styles.modalSuccessBtn}
                    >
                      Simulate Scan Success
                    </button>
                    <button 
                      onClick={() => {
                        setShowMockModal(false);
                        alert('QR Payment failed: Transaction declined by customer.');
                      }}
                      style={styles.modalFailBtn}
                    >
                      Simulate Scan Failure
                    </button>
                  </div>
                </div>
              )}

              {activeMockTab === 'methods' && (
                <div>
                  <div style={styles.modalMethods}>
                    <div style={styles.modalMethodRow}>
                      <span>💳 Cards (Visa, Mastercard, RuPay)</span>
                      <span style={styles.modalMethodCheck}>✓</span>
                    </div>
                    <div style={styles.modalMethodRow}>
                      <span>📱 UPI (GPay, PhonePe, Paytm)</span>
                      <span style={styles.modalMethodCheck}>✓</span>
                    </div>
                    <div style={styles.modalMethodRow}>
                      <span>🏛️ Netbanking / Wallets</span>
                      <span style={styles.modalMethodCheck}>✓</span>
                    </div>
                  </div>

                  <div style={styles.modalActions}>
                    <button 
                      onClick={() => {
                        setShowMockModal(false);
                        setCheckoutState('processing');
                        setProcessingMsg('Verifying mock payment...');
                        setTimeout(() => {
                          setProcessingMsg('Generating license keys...');
                          setTimeout(() => {
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
                            clearCart();
                          }, 1000);
                        }, 1000);
                      }}
                      style={styles.modalSuccessBtn}
                    >
                      Simulate Success
                    </button>
                    <button 
                      onClick={() => {
                        setShowMockModal(false);
                        alert('Payment failed: Mock transaction declined by user.');
                      }}
                      style={styles.modalFailBtn}
                    >
                      Simulate Failure
                    </button>
                  </div>
                </div>
              )}

              <div style={styles.modalFooter}>
                🔒 Secured by Simulated Razorpay
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default Checkout;
