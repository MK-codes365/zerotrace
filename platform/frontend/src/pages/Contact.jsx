import React, { useState } from 'react';
import './Contact.css';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: 'Technical Support',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState('');
  const [copied, setCopied] = useState(false);

  const pgpKeyFingerprint = "B6D2 7E1F A90C C534 8E01 9B4F 2F3C D9E7 56A8 1B2C";

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCopyFingerprint = () => {
    navigator.clipboard.writeText(pgpKeyFingerprint);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) return;

    setIsSubmitting(true);

    // Simulate cryptographic secure transmission handshake
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSubmitted(true);
      // Generate a random ticket ID
      const randomId = Math.floor(100000 + Math.random() * 900000);
      setTicketId(`ZT-${randomId}`);
    }, 1800);
  };

  const handleResetForm = () => {
    setFormData({
      name: '',
      email: '',
      subject: 'Technical Support',
      message: ''
    });
    setIsSubmitted(false);
    setTicketId('');
  };

  return (
    <div className="contact-wrapper">
      <div className="contact-glow-bg"></div>
      <div className="contact-glow-bg-left"></div>
      
      <div className="contact-container">
        <div className="contact-header">
          <h1 className="contact-title">Secure Communications</h1>
          <p className="contact-subtitle">
            Need technical assistance, custom enterprise solutions, or want to report a vulnerability? 
            Our security personnel are ready to respond.
          </p>
        </div>

        <div className="contact-grid">
          
          {/* Left Column: Info Cards */}
          <div className="contact-info-section">
            
            {/* Contact Channels */}
            <div className="contact-card">
              <h3 className="contact-card-title">
                <span>📞</span> Direct Channels
              </h3>
              <div className="contact-info-list">
                <div className="contact-info-item">
                  <div className="contact-info-icon">✉️</div>
                  <div className="contact-info-text">
                    <h4>Technical Support</h4>
                    <p><a href="mailto:support@zerotrace.io">support@zerotrace.io</a></p>
                  </div>
                </div>
                
                <div className="contact-info-item">
                  <div className="contact-info-icon">💼</div>
                  <div className="contact-info-text">
                    <h4>Enterprise Sales</h4>
                    <p><a href="mailto:enterprise@zerotrace.io">enterprise@zerotrace.io</a></p>
                  </div>
                </div>

                <div className="contact-info-item">
                  <div className="contact-info-icon">🐛</div>
                  <div className="contact-info-text">
                    <h4>Security / Bug Bounty</h4>
                    <p><a href="mailto:security@zerotrace.io">security@zerotrace.io</a></p>
                  </div>
                </div>
              </div>
            </div>

            {/* Security & Cryptography Info */}
            <div className="contact-card security-card">
              <h3 className="contact-card-title security-title">
                <span>🔒</span> Encrypted Contact
              </h3>
              <p className="security-desc">
                For sensitive inquiries or vulnerability reports, we recommend encrypting your communications 
                using our public PGP key.
              </p>
              <div className="pgp-box">
                <span className="pgp-label">PGP Key Fingerprint</span>
                <span className="pgp-fingerprint">{pgpKeyFingerprint}</span>
                <button 
                  onClick={handleCopyFingerprint} 
                  className={`copy-btn ${copied ? 'copied' : ''}`}
                >
                  {copied ? '✓ Copied' : '📄 Copy Fingerprint'}
                </button>
              </div>
            </div>

            {/* Operating Standards */}
            <div className="contact-card">
              <h3 className="contact-card-title">
                <span>⏱️</span> Response SLA
              </h3>
              <div className="contact-info-list">
                <div className="contact-info-item">
                  <div className="contact-info-icon">⚡</div>
                  <div className="contact-info-text">
                    <h4>SLA Guarantee</h4>
                    <p>Enterprise: Under 2 hours<br />Community: Under 12 hours</p>
                  </div>
                </div>
                
                <div className="contact-info-item">
                  <div className="contact-info-icon">🌍</div>
                  <div className="contact-info-text">
                    <h4>Operational Hours</h4>
                    <p>24/7/365 Security Monitoring & Incident Response</p>
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: Contact Form */}
          <div className="contact-card contact-form-card">
            {!isSubmitted ? (
              <>
                <h3 className="contact-card-title" style={{ marginBottom: '25px' }}>
                  <span>✉️</span> Transmission Console
                </h3>
                <form onSubmit={handleSubmit} className="contact-form">
                  <div className="form-row-2">
                    <div className="form-group">
                      <label htmlFor="name">Name</label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="John Doe"
                        className="form-input"
                        required
                        disabled={isSubmitting}
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="email">Email</label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="john@example.com"
                        className="form-input"
                        required
                        disabled={isSubmitting}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="subject">Inquiry Type</label>
                    <select
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      className="form-select"
                      disabled={isSubmitting}
                    >
                      <option value="Technical Support">Technical Support (Free/Pro)</option>
                      <option value="Enterprise Licensing">Enterprise Licensing & Quotes</option>
                      <option value="Bug Bounty Report">Vulnerability / Bug Bounty Report</option>
                      <option value="General Inquiry">General Inquiry</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="message">Message</label>
                    <textarea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Detail your request..."
                      className="form-textarea"
                      required
                      disabled={isSubmitting}
                    ></textarea>
                  </div>

                  <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={isSubmitting || !formData.name || !formData.email || !formData.message}
                  >
                    {isSubmitting ? (
                      <>
                        <div className="spinner"></div>
                        Establishing Secure Handshake...
                      </>
                    ) : (
                      'Send Secure Message'
                    )}
                  </button>
                </form>
              </>
            ) : (
              <div className="success-card">
                <div className="success-icon">🛡️</div>
                <h3 className="success-title">Message Transmitted</h3>
                <p className="success-message">
                  Your message has been encrypted and successfully sent to the ZeroTrace security database. 
                  A support agent will follow up shortly.
                </p>
                <div className="ticket-box">
                  <div className="ticket-label">Secure Ticket Reference</div>
                  <div className="ticket-id">{ticketId}</div>
                </div>
                <div>
                  <button onClick={handleResetForm} className="reset-btn">
                    Transmit Another Message
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default Contact;
