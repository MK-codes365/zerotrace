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
    contentLayout: {
      display: 'flex',
      gap: '40px',
      flexWrap: 'wrap',
    },
    cartItemsArea: {
      flex: '2',
      minWidth: '500px',
    },
    summaryArea: {
      flex: '1',
      minWidth: '320px',
    },
    // Table Styles
    table: {
      width: '100%',
      borderCollapse: 'collapse',
      background: 'var(--card-bg)',
      border: '1px solid #222',
      borderRadius: '12px',
      overflow: 'hidden',
    },
    th: {
      textAlign: 'left',
      padding: '15px 20px',
      borderBottom: '1px solid #2d2d2d',
      color: 'var(--text-secondary)',
      fontSize: '0.85rem',
      textTransform: 'uppercase',
      letterSpacing: '1px',
      background: '#151515',
    },
    tr: {
      borderBottom: '1px solid #1a1a1a',
    },
    td: {
      padding: '20px',
      verticalAlign: 'middle',
    },
    itemName: {
      fontWeight: '700',
      fontSize: '1.05rem',
      color: '#fff',
    },
    itemBilling: {
      fontSize: '0.8rem',
      color: 'var(--accent-primary)',
      marginTop: '4px',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    qtyControls: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
    },
    qtyBtn: {
      width: '28px',
      height: '28px',
      borderRadius: '4px',
      border: '1px solid #333',
      background: '#1d1d1d',
      color: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      fontSize: '1rem',
      transition: 'all 0.2s',
    },
    qtyNum: {
      fontSize: '1rem',
      fontWeight: '600',
      color: '#fff',
      minWidth: '20px',
      textAlign: 'center',
    },
    removeBtn: {
      background: 'transparent',
      border: 'none',
      color: 'var(--accent-danger)',
      cursor: 'pointer',
      fontSize: '1rem',
      padding: '5px',
      transition: 'opacity 0.2s',
    },
    // Summary Panel
    summaryCard: {
      background: 'var(--card-bg)',
      border: '1px solid #222',
      borderRadius: '12px',
      padding: '30px',
      position: 'sticky',
      top: '100px',
    },
    summaryTitle: {
      fontSize: '1.4rem',
      fontWeight: '700',
      color: '#fff',
      marginBottom: '20px',
      borderBottom: '1px solid #2d2d2d',
      paddingBottom: '12px',
    },
    summaryRow: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '15px',
      fontSize: '0.95rem',
      color: 'var(--text-secondary)',
    },
    totalRow: {
      display: 'flex',
      justifyContent: 'space-between',
      marginTop: '20px',
      paddingTop: '20px',
      borderTop: '1px solid #2d2d2d',
      fontSize: '1.25rem',
      fontWeight: '800',
      color: '#fff',
      marginBottom: '25px',
    },
    checkoutBtn: {
      width: '100%',
      padding: '15px',
      background: 'var(--accent-primary)',
      color: '#000',
      border: 'none',
      borderRadius: '8px',
      fontWeight: '700',
      fontSize: '1rem',
      cursor: 'pointer',
      transition: 'all 0.2s',
      boxShadow: '0 4px 15px rgba(0, 255, 157, 0.2)',
      textAlign: 'center',
      display: 'block',
      textDecoration: 'none',
    },
    continueLink: {
      display: 'block',
      textAlign: 'center',
      color: 'var(--text-secondary)',
      fontSize: '0.9rem',
      marginTop: '15px',
      textDecoration: 'none',
      transition: 'color 0.2s',
    },
    // Promo Form
    promoForm: {
      display: 'flex',
      gap: '10px',
      marginTop: '20px',
      borderTop: '1px solid #1a1a1a',
      paddingTop: '20px',
      marginBottom: '10px',
    },
    promoInput: {
      flex: 1,
      padding: '10px 15px',
      background: '#151515',
      border: '1px solid #2d2d2d',
      borderRadius: '6px',
      color: '#fff',
      fontSize: '0.9rem',
      outline: 'none',
    },
    promoBtn: {
      padding: '10px 20px',
      background: '#333',
      color: '#fff',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
      fontWeight: '600',
      fontSize: '0.85rem',
      transition: 'background 0.2s',
    },
    emptyState: {
      textAlign: 'center',
      padding: '60px 40px',
      background: 'var(--card-bg)',
      border: '1px solid #222',
      borderRadius: '12px',
      maxWidth: '600px',
      margin: '0 auto',
    },
    emptyIcon: {
      fontSize: '4rem',
      marginBottom: '20px',
      display: 'block',
    },
    emptyTitle: {
      fontSize: '1.6rem',
      color: '#fff',
      marginBottom: '10px',
    },
    emptyText: {
      color: 'var(--text-secondary)',
      marginBottom: '30px',
    },
    btnPrimary: {
      display: 'inline-block',
      padding: '12px 30px',
      background: 'var(--accent-primary)',
      color: '#000',
      borderRadius: '6px',
      fontWeight: '700',
      textDecoration: 'none',
      boxShadow: '0 4px 15px rgba(0, 255, 157, 0.2)',
    }
  };

  const handleCheckoutClick = () => {
    // Navigate to checkout and pass the discount info
    navigate('/checkout', { state: { discount } });
  };

  return (
    <div style={styles.page}>
      <div className="container">
        
        {cart.length === 0 ? (
          <div style={styles.emptyState}>
            <span style={styles.emptyIcon}>🛒</span>
            <h2 style={styles.emptyTitle}>Your Cart is Empty</h2>
            <p style={styles.emptyText}>You haven't added any license plans to your cart yet. Visit our pricing section to choose a plan.</p>
            <Link to="/" style={styles.btnPrimary}>View Pricing Plans</Link>
          </div>
        ) : (
          <>
            <h1 style={styles.title}>Your Shopping Cart</h1>
            <p style={styles.subtitle}>Review your license selections and proceed to secure checkout.</p>

            <div style={styles.contentLayout}>
              
              {/* Cart Table Area */}
              <div style={styles.cartItemsArea}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Product Details</th>
                      <th style={styles.th}>Price</th>
                      <th style={styles.th}>Quantity</th>
                      <th style={styles.th}>Total</th>
                      <th style={{...styles.th, width: '50px'}}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {cart.map((item) => (
                      <tr key={item.id} style={styles.tr}>
                        <td style={styles.td}>
                          <div style={styles.itemName}>{item.name}</div>
                          <div style={styles.itemBilling}>
                            {item.billingCycle === 'annual' ? 'Billed Annually' : 'Billed Monthly'}
                          </div>
                        </td>
                        <td style={{...styles.td, fontFamily: 'monospace', fontSize: '1rem', color: '#ccc'}}>
                          ${item.price}
                        </td>
                        <td style={styles.td}>
                          <div style={styles.qtyControls}>
                            <button 
                              style={styles.qtyBtn} 
                              onClick={() => updateQuantity(item.id, item.quantity - 1)}
                              disabled={item.quantity <= 1}
                            >
                              -
                            </button>
                            <span style={styles.qtyNum}>{item.quantity}</span>
                            <button 
                              style={styles.qtyBtn} 
                              onClick={() => updateQuantity(item.id, item.quantity + 1)}
                            >
                              +
                            </button>
                          </div>
                        </td>
                        <td style={{...styles.td, fontFamily: 'monospace', fontSize: '1.05rem', color: '#fff', fontWeight: 'bold'}}>
                          ${item.price * item.quantity}
                        </td>
                        <td style={{...styles.td, textAlign: 'center'}}>
                          <button 
                            style={styles.removeBtn} 
                            onClick={() => removeFromCart(item.id)}
                            title="Remove item"
                          >
                            🗑️
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Order Summary Sidebar */}
              <div style={styles.summaryArea}>
                <div style={styles.summaryCard}>
                  <h3 style={styles.summaryTitle}>Order Summary</h3>
                  
                  <div style={styles.summaryRow}>
                    <span>Subtotal</span>
                    <span style={{fontFamily: 'monospace'}}>${subtotal.toFixed(2)}</span>
                  </div>

                  {discount > 0 && (
                    <div style={{...styles.summaryRow, color: 'var(--accent-primary)'}}>
                      <span>Discount (20%)</span>
                      <span style={{fontFamily: 'monospace'}}>-${discountAmount.toFixed(2)}</span>
                    </div>
                  )}

                  <div style={styles.summaryRow}>
                    <span>VAT / Taxes (10%)</span>
                    <span style={{fontFamily: 'monospace'}}>${tax.toFixed(2)}</span>
                  </div>

                  <div style={styles.totalRow}>
                    <span>Total</span>
                    <span style={{color: 'var(--accent-primary)'}}>${total.toFixed(2)}</span>
                  </div>

                  <button 
                    onClick={handleCheckoutClick}
                    style={styles.checkoutBtn}
                  >
                    Proceed to Checkout
                  </button>
                  
                  <Link to="/" style={styles.continueLink}>
                    ← Continue Shopping
                  </Link>

                  {/* Coupon Promo form */}
                  <form onSubmit={handleApplyPromo} style={styles.promoForm}>
                    <input 
                      type="text" 
                      placeholder="Promo Code" 
                      value={promoCode} 
                      onChange={(e) => setPromoCode(e.target.value)}
                      style={styles.promoInput}
                    />
                    <button type="submit" style={styles.promoBtn}>Apply</button>
                  </form>
                  {promoError && (
                    <span style={{fontSize: '0.8rem', color: 'var(--accent-danger)'}}>{promoError}</span>
                  )}
                  {promoSuccess && (
                    <span style={{fontSize: '0.8rem', color: 'var(--accent-primary)', display: 'block', lineHeight: '1.4'}}>{promoSuccess}</span>
                  )}
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
