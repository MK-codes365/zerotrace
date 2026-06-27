import React from 'react';
import LegalLayout from '../components/LegalLayout';

const Terms = () => {
  return (
    <LegalLayout title="Terms and Conditions">
      <section style={{ marginBottom: '40px' }}>
        <h2 style={styles.heading}>1. Introduction</h2>
        <p>
          Welcome to ZeroTrace. By downloading, installing, or using our software, you agree to be bound by these Terms and Conditions. Please read them carefully before using our services.
        </p>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={styles.heading}>2. License Grant</h2>
        <p>
          ZeroTrace grants you a revocable, non-exclusive, non-transferable, limited license to download, install, and use the software strictly in accordance with the terms of this Agreement.
        </p>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={styles.heading}>3. Data Destruction</h2>
        <p>
          ZeroTrace is designed to permanently erase data. Once data is erased using this software, it cannot be recovered. You acknowledge that you use this software at your own risk and that ZeroTrace is not responsible for any accidental or intended loss of data.
        </p>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={styles.heading}>4. Limitation of Liability</h2>
        <p>
          In no event shall ZeroTrace, nor its directors, employees, partners, agents, suppliers, or affiliates, be liable for any indirect, incidental, special, consequential or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses.
        </p>
      </section>

      <section>
        <h2 style={styles.heading}>5. Changes to Terms</h2>
        <p>
          We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is material we will try to provide at least 30 days' notice prior to any new terms taking effect.
        </p>
      </section>
    </LegalLayout>
  );
};

const styles = {
  heading: {
    color: 'var(--text-primary)',
    marginBottom: '15px',
    fontSize: '1.5rem',
  }
};

export default Terms;
