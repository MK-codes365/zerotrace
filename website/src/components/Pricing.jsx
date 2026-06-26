import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';

const Pricing = () => {
  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' or 'annual'
  const [hoveredCard, setHoveredCard] = useState(null);
  const [hoveredBtn, setHoveredBtn] = useState(null);
  const { addToCart } = useCart();
  const navigate = useNavigate();

  const plans = [
    {
      id: 'community',
      name: 'Community',
      desc: 'Essential security for individual developers and privacy enthusiasts.',
      price: {
        monthly: 0,
        annual: 0,
      },
      features: [
        '1-Pass NIST Clear Wiping',
        'CustomTkinter Desktop UI',
        'C++ Performance Engine',
        'Local Wiping Verification logs',
        'Standard PDF/JSON certificates',
        'Community Forum Support',
      ],
      cta: 'Download Installer',
      badge: null,
      highlight: false,
    },
    {
      id: 'professional',
      name: 'Professional',
      desc: 'Advanced data destruction and priority tools for power users.',
      price: {
        monthly: 15,
        annual: 12,
      },
      features: [
        'All Community features',
        'Multi-Pass Sanitization (DoD 3/7-Pass, Gutmann 35-Pass)',
        'Unlimited Physical & Logical Drives',
        'Digitally Signed Verification Certificates',
        'Advanced Command Line Interface (CLI)',
        'Priority Email Support (24hr response)',
      ],
      cta: 'Get Pro License',
      badge: 'MOST POPULAR',
      highlight: true,
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      desc: 'Full-scale compliance, automation, and support for organizations.',
      price: {
        monthly: 119,
        annual: 99,
      },
      features: [
        'All Professional features',
        'Centralized Web Management Console',
        'Active Directory & Okta SSO Integration',
        'Automated Network & Cloud Drive Scanning',
        '24/7 Phone Support & Dedicated Account Manager',
        'Custom Regulatory Compliance Audit Logs',
        'Enterprise SLA Guarantee (99.9% uptime)',
      ],
      cta: 'Contact Sales',
      badge: 'ENTERPRISE READY',
      highlight: false,
    },
  ];

  const toggleBilling = (cycle) => {
    setBillingCycle(cycle);
  };

  const styles = {
    section: {
      padding: '100px 0',
      backgroundColor: '#0a0a0a', // Dark theme contrast
      borderTop: '1px solid #1a1a1a',
      borderBottom: '1px solid #1a1a1a',
      position: 'relative',
      overflow: 'hidden',
    },
    container: {
      position: 'relative',
      zIndex: 2,
    },
    headerArea: {
      textAlign: 'center',
      marginBottom: '50px',
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: '700',
      marginBottom: '15px',
      background: 'linear-gradient(45deg, #fff, #a0a0a0)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    subtitle: {
      fontSize: '1.1rem',
      color: 'var(--text-secondary)',
      maxWidth: '600px',
      margin: '0 auto 30px',
    },
    // Billing Toggle Styles
    toggleContainer: {
      display: 'inline-flex',
      alignItems: 'center',
      background: '#151515',
      border: '1px solid #2d2d2d',
      borderRadius: '50px',
      padding: '4px',
      position: 'relative',
    },
    toggleBtn: {
      padding: '10px 24px',
      borderRadius: '50px',
      fontSize: '0.9rem',
      fontWeight: '600',
      border: 'none',
      background: 'transparent',
      color: 'var(--text-secondary)',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      zIndex: 2,
    },
    toggleBtnActive: {
      color: '#000',
    },
    toggleSlider: {
      position: 'absolute',
      top: '4px',
      height: 'calc(100% - 8px)',
      background: 'var(--accent-primary)',
      borderRadius: '50px',
      transition: 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      zIndex: 1,
      boxShadow: '0 0 10px rgba(0, 255, 157, 0.3)',
    },
    // Grid layout
    grid: {
      display: 'flex',
      justifyContent: 'center',
      gap: '30px',
      flexWrap: 'wrap',
      marginTop: '20px',
    },
    // Card styles
    card: {
      background: 'var(--card-bg)',
      border: '1px solid #222',
      borderRadius: '16px',
      padding: '40px 30px',
      width: '350px',
      position: 'relative',
      transition: 'all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      display: 'flex',
      flexDirection: 'column',
    },
    cardHighlight: {
      borderColor: 'var(--accent-primary)',
      boxShadow: '0 0 25px rgba(0, 255, 157, 0.15)',
      transform: 'translateY(-5px)',
    },
    cardHover: {
      transform: 'translateY(-10px)',
      boxShadow: '0 15px 30px rgba(0,0,0,0.5)',
      borderColor: '#3a3a3a',
    },
    cardHighlightHover: {
      transform: 'translateY(-12px)',
      boxShadow: '0 20px 40px rgba(0, 255, 157, 0.25)',
      borderColor: 'var(--accent-primary)',
    },
    badge: {
      position: 'absolute',
      top: '-15px',
      left: '50%',
      transform: 'translateX(-50%)',
      padding: '6px 16px',
      borderRadius: '20px',
      fontSize: '0.75rem',
      fontWeight: '700',
      letterSpacing: '1px',
      textTransform: 'uppercase',
      background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
      color: '#000',
      boxShadow: '0 0 10px rgba(0, 255, 157, 0.4)',
    },
    badgeEnterprise: {
      background: '#222',
      color: '#fff',
      border: '1px solid #444',
      boxShadow: 'none',
    },
    planName: {
      fontSize: '1.6rem',
      fontWeight: '700',
      color: '#fff',
      marginBottom: '10px',
    },
    planDesc: {
      fontSize: '0.9rem',
      color: 'var(--text-secondary)',
      marginBottom: '25px',
      minHeight: '45px',
      lineHeight: '1.5',
    },
    // Price Styling
    priceContainer: {
      marginBottom: '30px',
      display: 'flex',
      alignItems: 'baseline',
    },
    priceNumber: {
      fontSize: '3rem',
      fontWeight: '800',
      color: '#fff',
      transition: 'opacity 0.2s, transform 0.2s',
    },
    pricePeriod: {
      fontSize: '0.95rem',
      color: 'var(--text-secondary)',
      marginLeft: '5px',
    },
    featureList: {
      listStyle: 'none',
      padding: 0,
      margin: '0 0 35px 0',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      flex: 1,
    },
    featureItem: {
      fontSize: '0.9rem',
      color: '#ccc',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      lineHeight: '1.4',
    },
    checkIcon: {
      color: 'var(--accent-primary)',
      fontWeight: 'bold',
      fontSize: '1rem',
      flexShrink: 0,
    },
    ctaBtn: {
      padding: '14px 0',
      width: '100%',
      borderRadius: '8px',
      fontWeight: '700',
      fontSize: '0.95rem',
      cursor: 'pointer',
      textAlign: 'center',
      border: 'none',
      transition: 'all 0.2s ease',
    },
    ctaBtnStandard: {
      background: '#202020',
      color: '#fff',
      border: '1px solid #333',
    },
    ctaBtnHighlight: {
      background: 'var(--accent-primary)',
      color: '#000',
      boxShadow: '0 4px 15px rgba(0, 255, 157, 0.2)',
    },
    ctaBtnStandardHover: {
      background: '#2b2b2b',
      borderColor: '#444',
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    },
    ctaBtnHighlightHover: {
      background: '#05ff9e',
      transform: 'scale(1.02)',
      boxShadow: '0 6px 20px rgba(0, 255, 157, 0.4)',
    },
    savingsLabel: {
      fontSize: '0.8rem',
      color: 'var(--accent-primary)',
      marginTop: '10px',
      display: 'block',
      fontWeight: '600',
    }
  };

  return (
    <section style={styles.section} id="pricing">
      <div className="container" style={styles.container}>
        
        <div style={styles.headerArea}>
          <h2 style={styles.title}>Simple, Transparent Pricing</h2>
          <p style={styles.subtitle}>
            Choose the plan that matches your security requirements. Open-source core, always.
          </p>

          {/* Custom Billing Toggle */}
          <div style={styles.toggleContainer}>
            <button
              onClick={() => toggleBilling('monthly')}
              style={{
                ...styles.toggleBtn,
                ...(billingCycle === 'monthly' ? styles.toggleBtnActive : {}),
              }}
            >
              Monthly
            </button>
            <button
              onClick={() => toggleBilling('annual')}
              style={{
                ...styles.toggleBtn,
                ...(billingCycle === 'annual' ? styles.toggleBtnActive : {}),
              }}
            >
              Annual (Save 20%)
            </button>

            {/* Sliding Slider background block */}
            <div
              style={{
                ...styles.toggleSlider,
                left: billingCycle === 'monthly' ? '4px' : '108px',
                width: billingCycle === 'monthly' ? '104px' : '162px',
              }}
            ></div>
          </div>
        </div>

        {/* Pricing Cards Grid */}
        <div style={styles.grid}>
          {plans.map((plan) => {
            const isHovered = hoveredCard === plan.id;
            const isBtnHovered = hoveredBtn === plan.id;
            const currentPrice = billingCycle === 'monthly' ? plan.price.monthly : plan.price.annual;

            // Compute dynamic card style
            let cardStyle = { ...styles.card };
            if (plan.highlight) {
              cardStyle = { ...cardStyle, ...styles.cardHighlight };
              if (isHovered) {
                cardStyle = { ...cardStyle, ...styles.cardHighlightHover };
              }
            } else if (isHovered) {
              cardStyle = { ...cardStyle, ...styles.cardHover };
            }

            // Compute dynamic button style
            let btnStyle = { ...styles.ctaBtn };
            if (plan.highlight) {
              btnStyle = { ...btnStyle, ...styles.ctaBtnHighlight };
              if (isBtnHovered) {
                btnStyle = { ...btnStyle, ...styles.ctaBtnHighlightHover };
              }
            } else {
              btnStyle = { ...btnStyle, ...styles.ctaBtnStandard };
              if (isBtnHovered) {
                btnStyle = { ...btnStyle, ...styles.ctaBtnStandardHover };
              }
            }

            return (
              <div
                key={plan.id}
                style={cardStyle}
                onMouseEnter={() => setHoveredCard(plan.id)}
                onMouseLeave={() => setHoveredCard(null)}
              >
                {/* Badge for highlighted plans */}
                {plan.badge && (
                  <div style={{
                    ...styles.badge, 
                    ...(plan.id === 'enterprise' ? styles.badgeEnterprise : {})
                  }}>
                    {plan.badge}
                  </div>
                )}

                <h3 style={styles.planName}>{plan.name}</h3>
                <p style={styles.planDesc}>{plan.desc}</p>

                {/* Price displays */}
                <div style={styles.priceContainer}>
                  <span style={styles.priceNumber}>
                    {plan.price.monthly === 0 ? '$0' : `$${currentPrice}`}
                  </span>
                  {plan.price.monthly > 0 && (
                    <span style={styles.pricePeriod}>/ month</span>
                  )}
                </div>

                {/* Bullet Points */}
                <ul style={styles.featureList}>
                  {plan.features.map((feature, index) => (
                    <li key={index} style={styles.featureItem}>
                      <span style={styles.checkIcon}>✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Action Button */}
                <button
                  style={btnStyle}
                  onMouseEnter={() => setHoveredBtn(plan.id)}
                  onMouseLeave={() => setHoveredBtn(null)}
                  onClick={() => {
                    if (plan.id === 'community') {
                      document.getElementById('downloads')?.scrollIntoView({ behavior: 'smooth' });
                    } else {
                      addToCart(plan, billingCycle);
                      navigate('/cart');
                    }
                  }}
                >
                  {plan.cta}
                </button>

                {/* Savings Notice */}
                {billingCycle === 'annual' && plan.price.monthly > 0 && (
                  <span style={styles.savingsLabel}>
                    Save ${ (plan.price.monthly - plan.price.annual) * 12 }/yr (billed annually)
                  </span>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
};

export default Pricing;
