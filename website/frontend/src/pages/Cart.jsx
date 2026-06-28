import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';

const Cart = () => {
  const { cart, removeFromCart, updateQuantity, getCartTotal } = useCart();
  const navigate = useNavigate();
  const [promoCode, setPromoCode] = useState('');
  const [discount, setDiscount] = useState(0);
  const [promoError, setPromoError] = useState('');
  const [promoSuccess, setPromoSuccess] = useState('');

  const handleApplyPromo = (e) => {
    e.preventDefault();
    setPromoError('');
    setPromoSuccess('');

    if (promoCode.trim().toUpperCase() === 'ZEROTRACE20') {
      setDiscount(0.20); // 20% discount
      setPromoSuccess('Promo code ZEROTRACE20 applied! 20% discount has been subtracted.');
    } else if (promoCode.trim() === '') {
      setPromoError('Please enter a promo code.');
    } else {
      setPromoError('Invalid promo code. Try ZEROTRACE20');
    }
  };

  const subtotal = getCartTotal();
  const discountAmount = subtotal * discount;
  const taxRate = 0.10; // 10% VAT
  const tax = (subtotal - discountAmount) * taxRate;
  const total = subtotal - discountAmount + tax;

  const handleCheckoutClick = () => {
    navigate('/checkout', { state: { discount } });
  };

  const getPlanIcon = (planId) => {
    switch (planId) {
      case 'community':
        return (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-secondary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <circle cx="12" cy="11" r="3" />
          </svg>
        );
      case 'professional':
        return (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="m9 11 2 2 4-4" />
          </svg>
        );
      case 'enterprise':
        return (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c77dff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <rect x="9" y="8" width="6" height="8" rx="1" />
            <path d="M12 11h.01" />
          </svg>
        );
      default:
        return (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        );
    }
  };

  const styles = {
    page: {
      minHeight: '100vh',
      padding: '140px 0 80px',
      background: 'radial-gradient(circle at top, #0f0f0f 0%, #050505 100%)',
      color: 'var(--text-primary)',
      fontFamily: 'var(--font-main)',
    },
    headerSection: {
      textAlign: 'center',
      marginBottom: '40px',
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: '800',
      marginBottom: '10px',
      background: 'linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      letterSpacing: '-0.5px',
    },
    subtitle: {
      fontSize: '1.05rem',
      color: 'var(--text-secondary)',
      maxWidth: '500px',
      margin: '0 auto',
    },
    stepperContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '20px',
      margin: '0 auto 50px',
      maxWidth: '600px',
      padding: '0 20px',
    },
    step: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      opacity: 0.4,
      transition: 'all 0.3s ease',
    },
    stepActive: {
      opacity: 1,
    },
    stepNum: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '24px',
      height: '24px',
      borderRadius: '50%',
      border: '1px solid rgba(255, 255, 255, 0.4)',
      fontSize: '0.8rem',
      fontWeight: '700',
      color: 'var(--text-secondary)',
    },
    stepNumActive: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '24px',
      height: '24px',
      borderRadius: '50%',
      background: 'var(--accent-primary)',
      border: '1px solid var(--accent-primary)',
      fontSize: '0.8rem',
      fontWeight: '700',
      color: '#000',
      boxShadow: '0 0 10px rgba(0, 255, 157, 0.4)',
    },
    stepLabel: {
      fontSize: '0.9rem',
      fontWeight: '500',
      color: 'var(--text-secondary)',
    },
    stepLabelActive: {
      fontSize: '0.9rem',
      fontWeight: '700',
      color: '#fff',
    },
    stepLine: {
      flex: 1,
      height: '1px',
      background: 'rgba(255, 255, 255, 0.1)',
    },
    contentLayout: {
      display: 'flex',
      gap: '40px',
      alignItems: 'flex-start',
    },
    cartItemsArea: {
      flex: '1.7',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
    },
    summaryArea: {
      flex: '1',
      minWidth: '340px',
    },
    cartItemCard: {
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
    },
    itemHeader: {
      display: 'flex',
      gap: '16px',
      alignItems: 'flex-start',
    },
    itemIconContainer: {
      padding: '12px',
      borderRadius: '10px',
      background: 'rgba(255, 255, 255, 0.03)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    },
    itemInfo: {
      flex: 1,
    },
    planBadge: (planId) => {
      let color = 'var(--accent-secondary)';
      let bg = 'rgba(0, 184, 255, 0.1)';
      let border = 'rgba(0, 184, 255, 0.2)';
      if (planId === 'professional') {
        color = 'var(--accent-primary)';
        bg = 'rgba(0, 255, 157, 0.1)';
        border = 'rgba(0, 255, 157, 0.2)';
      } else if (planId === 'enterprise') {
        color = '#c77dff';
        bg = 'rgba(199, 125, 255, 0.1)';
        border = 'rgba(199, 125, 255, 0.2)';
      }
      return {
        display: 'inline-block',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '0.7rem',
        fontWeight: '700',
        letterSpacing: '1px',
        color: color,
        background: bg,
        border: `1px solid ${border}`,
        marginBottom: '8px',
      };
    },
    itemName: {
      fontSize: '1.2rem',
      fontWeight: '700',
      color: '#fff',
      margin: '0 0 4px',
    },
    itemBilling: {
      fontSize: '0.85rem',
      color: 'var(--text-secondary)',
      margin: 0,
    },
    itemFooter: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderTop: '1px solid rgba(255, 255, 255, 0.05)',
      paddingTop: '20px',
      flexWrap: 'wrap',
      gap: '16px',
    },
    qtyContainer: {
      display: 'flex',
      flexDirection: 'column',
      gap: '6px',
    },
    itemLabel: {
      fontSize: '0.75rem',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      color: 'var(--text-secondary)',
    },
    qtyControls: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
    },
    qtyNum: {
      fontSize: '1.1rem',
      fontWeight: '600',
      color: '#fff',
      minWidth: '24px',
      textAlign: 'center',
    },
    itemPricing: {
      display: 'flex',
      gap: '24px',
    },
    priceRow: {
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
      alignItems: 'flex-start',
    },
    unitPrice: {
      fontFamily: '"SFMono-Regular", Consolas, monospace',
      fontSize: '0.95rem',
      color: 'var(--text-secondary)',
    },
    subtotalPrice: {
      fontFamily: '"SFMono-Regular", Consolas, monospace',
      fontSize: '1.1rem',
      fontWeight: '700',
      color: 'var(--accent-primary)',
    },
    // Summary Sidebar
    summaryCard: {
      padding: '30px',
      position: 'sticky',
      top: '100px',
    },
    summaryTitle: {
      fontSize: '1.25rem',
      fontWeight: '700',
      color: '#fff',
      marginBottom: '20px',
      letterSpacing: '0.5px',
      textTransform: 'uppercase',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      paddingBottom: '14px',
    },
    summaryRow: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '16px',
      fontSize: '0.95rem',
      color: 'var(--text-secondary)',
    },
    totalRow: {
      display: 'flex',
      justifyContent: 'space-between',
      marginTop: '20px',
      paddingTop: '20px',
      borderTop: '1px solid rgba(255, 255, 255, 0.08)',
      fontSize: '1.3rem',
      fontWeight: '800',
      color: '#fff',
      marginBottom: '24px',
    },
    continueLink: {
      display: 'block',
      textAlign: 'center',
      color: 'var(--text-secondary)',
      fontSize: '0.9rem',
      marginTop: '16px',
      textDecoration: 'none',
      transition: 'color 0.2s',
    },
    promoForm: {
      display: 'flex',
      gap: '10px',
      marginTop: '24px',
      borderTop: '1px solid rgba(255, 255, 255, 0.08)',
      paddingTop: '24px',
      marginBottom: '12px',
    },
    securityBadges: {
      marginTop: '24px',
      borderTop: '1px solid rgba(255, 255, 255, 0.08)',
      paddingTop: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
    },
    securityBadge: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      fontSize: '0.8rem',
      color: 'var(--text-secondary)',
    },
    securityIcon: {
      color: 'var(--accent-primary)',
      display: 'flex',
      alignItems: 'center',
    },
    emptyState: {
      textAlign: 'center',
      padding: '80px 40px',
      maxWidth: '550px',
      margin: '0 auto',
    },
    emptyTitle: {
      fontSize: '1.75rem',
      fontWeight: '700',
      color: '#fff',
      marginBottom: '12px',
    },
    emptyText: {
      color: 'var(--text-secondary)',
      fontSize: '0.95rem',
      lineHeight: '1.6',
      marginBottom: '32px',
    },
  };

  return (
    <div style={styles.page}>
      {/* Inject custom CSS styles for animations and hovers */}
      <style>{`
        .cyber-card {
          background: rgba(17, 17, 17, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        }
        .cyber-card:hover {
          border-color: rgba(0, 255, 157, 0.3);
          box-shadow: 0 10px 40px rgba(0, 255, 157, 0.06);
          transform: translateY(-2px);
        }
        .qty-btn {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(30, 30, 30, 0.6);
          color: #fff;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-size: 1.1rem;
          transition: all 0.2s ease;
        }
        .qty-btn:hover:not(:disabled) {
          border-color: var(--accent-primary);
          background: rgba(0, 255, 157, 0.1);
          color: var(--accent-primary);
          box-shadow: 0 0 10px rgba(0, 255, 157, 0.2);
        }
        .qty-btn:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }
        .remove-btn {
          background: rgba(255, 77, 77, 0.05);
          border: 1px solid rgba(255, 77, 77, 0.15);
          color: var(--accent-danger);
          border-radius: 8px;
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .remove-btn:hover {
          background: var(--accent-danger);
          color: #fff;
          box-shadow: 0 0 15px rgba(255, 77, 77, 0.4);
          border-color: var(--accent-danger);
        }
        .checkout-btn {
          width: 100%;
          padding: 16px;
          background: linear-gradient(135deg, var(--accent-primary) 0%, #00d9ff 100%);
          color: #000;
          border: none;
          border-radius: 8px;
          font-weight: 700;
          font-size: 1.05rem;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          box-shadow: 0 4px 20px rgba(0, 255, 157, 0.25);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .checkout-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 30px rgba(0, 255, 157, 0.4);
        }
        .promo-input {
          flex: 1;
          padding: 12px 16px;
          background: rgba(20, 20, 20, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: #fff;
          font-size: 0.95rem;
          outline: none;
          transition: all 0.2s ease;
        }
        .promo-input:focus {
          border-color: var(--accent-primary);
          box-shadow: 0 0 10px rgba(0, 255, 157, 0.15);
          background: rgba(25, 25, 25, 0.9);
        }
        .promo-btn {
          padding: 12px 20px;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #fff;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.9rem;
          transition: all 0.2s ease;
        }
        .promo-btn:hover {
          background: #fff;
          color: #000;
        }
        .btn-primary {
          display: inline-block;
          padding: 14px 32px;
          background: linear-gradient(135deg, var(--accent-primary) 0%, #00d9ff 100%);
          color: #000;
          border-radius: 8px;
          font-weight: 700;
          font-size: 0.95rem;
          text-decoration: none;
          box-shadow: 0 4px 20px rgba(0, 255, 157, 0.25);
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 30px rgba(0, 255, 157, 0.4);
        }
        .pulse-glow {
          animation: pulse-glow-anim 2s infinite ease-in-out;
        }
        @keyframes pulse-glow-anim {
          0% {
            filter: drop-shadow(0 0 5px rgba(0, 255, 157, 0.2));
          }
          50% {
            filter: drop-shadow(0 0 15px rgba(0, 255, 157, 0.4));
          }
          100% {
            filter: drop-shadow(0 0 5px rgba(0, 255, 157, 0.2));
          }
        }
        .empty-vault {
          animation: vault-float 4s infinite ease-in-out;
        }
        @keyframes vault-float {
          0% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-8px);
          }
          100% {
            transform: translateY(0px);
          }
        }
        .continue-shopping-link {
          transition: all 0.2s ease;
        }
        .continue-shopping-link:hover {
          color: #fff !important;
          text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
        }
        @media (max-width: 992px) {
          .cart-layout {
            flex-direction: column !important;
            gap: 30px !important;
          }
          .cart-items-area {
            min-width: 100% !important;
          }
          .summary-area {
            min-width: 100% !important;
          }
        }
      `}</style>

      <div className="container">
        
        {cart.length === 0 ? (
          <div className="cyber-card" style={styles.emptyState}>
            <div className="empty-vault" style={{ display: 'inline-block', marginBottom: '24px' }}>
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="rgba(0, 255, 157, 0.4)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" className="pulse-glow">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="12" cy="12" r="6" strokeDasharray="3 3" />
                <circle cx="12" cy="12" r="3" />
                <path d="M12 3v3" />
                <path d="M12 18v3" />
                <path d="M3 12h3" />
                <path d="M18 12h3" />
              </svg>
            </div>
            <h2 style={styles.emptyTitle}>Your Cart is Empty</h2>
            <p style={styles.emptyText}>You haven't added any license plans to your cart yet. Visit our pricing section to choose a plan and secure your digital footprint.</p>
            <Link to="/" className="btn-primary">View Pricing Plans</Link>
          </div>
        ) : (
          <>
            <div style={styles.headerSection}>
              <h1 style={styles.title}>Secure Cart</h1>
              <p style={styles.subtitle}>Review your digital sanitization suites before proceeding.</p>
            </div>

            {/* Stepper Progress Indicator */}
            <div style={styles.stepperContainer}>
              <div style={{ ...styles.step, ...styles.stepActive }}>
                <span style={styles.stepNumActive}>1</span>
                <span style={styles.stepLabelActive}>Cart Review</span>
              </div>
              <div style={styles.stepLine}></div>
              <div style={styles.step}>
                <span style={styles.stepNum}>2</span>
                <span style={styles.stepLabel}>Checkout</span>
              </div>
              <div style={styles.stepLine}></div>
              <div style={styles.step}>
                <span style={styles.stepNum}>3</span>
                <span style={styles.stepLabel}>Deployment</span>
              </div>
            </div>

            <div className="cart-layout" style={styles.contentLayout}>
              
              {/* Cart List cards */}
              <div className="cart-items-area" style={styles.cartItemsArea}>
                {cart.map((item) => {
                  const planId = item.planId || (item.id.includes('community') ? 'community' : item.id.includes('professional') ? 'professional' : 'enterprise');
                  return (
                    <div key={item.id} className="cyber-card" style={styles.cartItemCard}>
                      <div style={styles.itemHeader}>
                        <div style={styles.itemIconContainer}>
                          {getPlanIcon(planId)}
                        </div>
                        <div style={styles.itemInfo}>
                          <span style={styles.planBadge(planId)}>
                            {planId.toUpperCase()} EDITION
                          </span>
                          <h3 style={styles.itemName}>{item.name}</h3>
                          <p style={styles.itemBilling}>
                            {item.billingCycle === 'annual' ? '⚡ Billed Annually (Save 20%)' : '📅 Billed Monthly'}
                          </p>
                        </div>
                      </div>

                      <div style={styles.itemFooter}>
                        {/* Quantity Controls */}
                        <div style={styles.qtyContainer}>
                          <span style={styles.itemLabel}>Quantity</span>
                          <div style={styles.qtyControls}>
                            <button 
                              className="qty-btn" 
                              onClick={() => updateQuantity(item.id, item.quantity - 1)}
                              disabled={item.quantity <= 1}
                            >
                              -
                            </button>
                            <span style={styles.qtyNum}>{item.quantity}</span>
                            <button 
                              className="qty-btn" 
                              onClick={() => updateQuantity(item.id, item.quantity + 1)}
                            >
                              +
                            </button>
                          </div>
                        </div>

                        {/* Price Details */}
                        <div style={styles.itemPricing}>
                          <div style={styles.priceRow}>
                            <span style={styles.itemLabel}>Unit Price</span>
                            <span style={styles.unitPrice}>₹{item.price.toLocaleString('en-IN')}.00</span>
                          </div>
                          <div style={styles.priceRow}>
                            <span style={styles.itemLabel}>Subtotal</span>
                            <span style={styles.subtotalPrice}>₹{(item.price * item.quantity).toLocaleString('en-IN')}.00</span>
                          </div>
                        </div>

                        {/* Remove Action */}
                        <button 
                          className="remove-btn" 
                          onClick={() => removeFromCart(item.id)}
                          title="Remove item"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                          </svg>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Order Summary Sidebar */}
              <div className="summary-area" style={styles.summaryArea}>
                <div className="cyber-card" style={styles.summaryCard}>
                  <h3 style={styles.summaryTitle}>Transaction Summary</h3>
                  
                  <div style={styles.summaryRow}>
                    <span>Subtotal</span>
                    <span style={{ fontFamily: '"SFMono-Regular", Consolas, monospace', color: '#fff' }}>
                      ₹{subtotal.toLocaleString('en-IN')}.00
                    </span>
                  </div>

                  {discount > 0 && (
                    <div style={{ ...styles.summaryRow, color: 'var(--accent-primary)' }}>
                      <span>Promo Discount (20%)</span>
                      <span style={{ fontFamily: '"SFMono-Regular", Consolas, monospace' }}>
                        -₹{discountAmount.toLocaleString('en-IN')}.00
                      </span>
                    </div>
                  )}

                  <div style={styles.summaryRow}>
                    <span>Regulatory Tax / VAT (10%)</span>
                    <span style={{ fontFamily: '"SFMono-Regular", Consolas, monospace', color: '#fff' }}>
                      ₹{tax.toLocaleString('en-IN')}.00
                    </span>
                  </div>

                  <div style={styles.totalRow}>
                    <span>Grand Total</span>
                    <span style={{ color: 'var(--accent-primary)', fontFamily: '"SFMono-Regular", Consolas, monospace' }}>
                      ₹{total.toLocaleString('en-IN')}.00
                    </span>
                  </div>

                  <button 
                    onClick={handleCheckoutClick}
                    className="checkout-btn"
                  >
                    Proceed to Checkout
                  </button>
                  
                  <Link to="/" className="continue-shopping-link" style={styles.continueLink}>
                    ← Return to Home
                  </Link>

                  {/* Promo Form */}
                  <form onSubmit={handleApplyPromo} style={styles.promoForm}>
                    <input 
                      type="text" 
                      placeholder="Promo Code (e.g. ZEROTRACE20)" 
                      value={promoCode} 
                      onChange={(e) => setPromoCode(e.target.value)}
                      className="promo-input"
                    />
                    <button type="submit" className="promo-btn">Apply</button>
                  </form>
                  {promoError && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--accent-danger)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span>⚠️</span> {promoError}
                    </div>
                  )}
                  {promoSuccess && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', marginTop: '4px', display: 'block', lineHeight: '1.4' }}>
                      🛡️ {promoSuccess}
                    </div>
                  )}

                  {/* Trust/Security badges */}
                  <div style={styles.securityBadges}>
                    <div style={styles.securityBadge}>
                      <span style={styles.securityIcon}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        </svg>
                      </span>
                      <span>AES-256 SSL Encrypted Connection</span>
                    </div>
                    <div style={styles.securityBadge}>
                      <span style={styles.securityIcon}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                        </svg>
                      </span>
                      <span>Instant Digital Cryptographic Delivery</span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </>
        )}

      </div>
    </div>
  );
};

export default Cart;
