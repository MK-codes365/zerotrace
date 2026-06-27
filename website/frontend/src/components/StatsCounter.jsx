import React, { useState, useEffect } from 'react';

const StatsCounter = () => {
  const [stats, setStats] = useState({
    filesWiped: '0',
    dataSecured: '0B',
    activeUsers: '0'
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/stats');
        if (!res.ok) return;
        const data = await res.json();

        // Format files count (e.g., 10453920 to 10.4M+)
        const files = data.filesWiped;
        let filesFormatted = '0';
        if (files >= 1000000) {
          filesFormatted = `${(files / 1000000).toFixed(1)}M+`;
        } else if (files >= 1000) {
          filesFormatted = `${(files / 1000).toFixed(1)}k+`;
        } else {
          filesFormatted = files.toString();
        }

        // Format bytes count to TB or GB
        const bytes = data.bytesWiped;
        let dataFormatted = '0B';
        const tb = bytes / (1024 * 1024 * 1024 * 1024);
        if (tb >= 1) {
          dataFormatted = `${tb.toFixed(1)}TB`;
        } else {
          const gb = bytes / (1024 * 1024 * 1024);
          dataFormatted = `${gb.toFixed(1)}GB`;
        }

        // Format active users count
        const users = data.activeUsers;
        let usersFormatted = '0';
        if (users >= 1000000) {
          usersFormatted = `${(users / 1000000).toFixed(1)}M+`;
        } else if (users >= 1000) {
          usersFormatted = `${(users / 1000).toFixed(1)}k+`;
        } else {
          usersFormatted = users.toString();
        }

        setStats({
          filesWiped: filesFormatted,
          dataSecured: dataFormatted,
          activeUsers: usersFormatted
        });
      } catch (err) {
        // Fall back silently to default values if server is offline
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section style={styles.section}>
      <div className="container">
        <div style={styles.grid}>
          <div style={styles.item}>
            <div style={styles.number}>{stats.filesWiped}</div>
            <div style={styles.label}>Files Wiped</div>
          </div>
          <div style={styles.item}>
            <div style={styles.number}>{stats.dataSecured}</div>
            <div style={styles.label}>Data Secured</div>
          </div>
          <div style={styles.item}>
            <div style={styles.number}>100%</div>
            <div style={styles.label}>NIST Compliant</div>
          </div>
          <div style={styles.item}>
            <div style={styles.number}>{stats.activeUsers}</div>
            <div style={styles.label}>Active Users</div>
          </div>
        </div>
      </div>
    </section>
  );
};

const styles = {
  section: {
    padding: '60px 0',
    background: 'linear-gradient(90deg, #111 0%, #050505 100%)',
    borderTop: '1px solid #222',
    borderBottom: '1px solid #222',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '30px',
    textAlign: 'center',
  },
  number: {
    fontSize: '3rem',
    fontWeight: '800',
    backgroundImage: 'linear-gradient(45deg, #fff, #666)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: '5px',
  },
  label: {
    color: 'var(--accent-primary)',
    fontSize: '1rem',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    fontWeight: '600',
  }
};

export default StatsCounter;
