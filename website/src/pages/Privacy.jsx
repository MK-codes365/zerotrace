import React from 'react';
import LegalLayout from '../components/LegalLayout';

const Privacy = () => {
  return (
    <LegalLayout title="Privacy Policy">
      <section style={{ marginBottom: '40px' }}>
        <h2 style={styles.heading}>1. Information Collection</h2>
        <p>
          ZeroTrace respects your privacy. We do not collect, store, or transmit any of your personal files or data that you choose to erase using our software. The erasure process happens entirely locally on your machine.
        </p>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={styles.heading}>2. Usage Data</h2>
        <p>
          We may collect anonymous usage statistics (such as crash reports or successful wipe counts) to improve the stability and performance of our software. This data is aggregated and does not identify any individual user.
        </p>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={styles.heading}>3. Third-Party Services</h2>
        <p>
          Our website may contain links to third-party web sites or services that are not owned or controlled by ZeroTrace. We have no control over and assume no responsibility for the content, privacy policies or practices of any third party web sites or services.
        </p>
      </section>

      <section>
        <h2 style={styles.heading}>4. Contact Us</h2>
        <p>
          If you have any questions about this Privacy Policy, please contact us at support@zerotrace.com.
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

export default Privacy;
