import React, { useState, useEffect, useRef } from 'react';

const WipeSimulator = () => {
  // State management for simulator
  const [selectedDrive, setSelectedDrive] = useState(null);
  const [wipeMethod, setWipeMethod] = useState("NIST 800-88 Clear");
  const [simState, setSimState] = useState("idle"); // idle, confirm1, confirm2, wiping, complete, viewingCert
  const [progress, setProgress] = useState(0);
  const [currentPass, setCurrentPass] = useState(1);
  const [totalPasses, setTotalPasses] = useState(1);
  const [statusText, setStatusText] = useState("");
  const [logs, setLogs] = useState([]);
  const [speed, setSpeed] = useState(0);
  const [certId, setCertId] = useState("");

  const consoleRef = useRef(null);

  // Mock drive list matching the actual desktop app logic
  const mockDrives = [
    { id: 1, letter: "C", label: "Windows OS", size: "128 GB", isSystem: true },
    { id: 2, letter: "D", label: "External Backup", size: "512 GB", isSystem: false, model: "Seagate Expansion HDD" },
    { id: 3, letter: "E", label: "Secure Vault", size: "64 GB", isSystem: false, model: "SanDisk Extreme USB" },
    { id: 4, letter: "F", label: "Confidential SSD", size: "250 GB", isSystem: false, model: "Samsung 980 NVMe SSD" }
  ];

  const wipeMethods = [
    { name: "NIST 800-88 Clear", passes: 1, desc: "Quick single pass overwrite with zeros (0x00)" },
    { name: "NIST 800-88-2 Purge", passes: 1, desc: "Single pass random write with hardware entropy verification" },
    { name: "DoD 5220.22-M (3-Pass)", passes: 3, desc: "Pass 1: Zeros, Pass 2: Ones, Pass 3: Random" },
    { name: "DoD 5220.22-M ECE (7-Pass)", passes: 7, desc: "Alternating characters and random passes" },
    { name: "Peter Gutmann (35-Pass)", passes: 35, desc: "35 passes of alternating and random overwrite sequences" }
  ];

  // Auto-scroll logs inside container only (prevents full page jumping/scrolling)
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs]);

  // Determine total passes when method changes
  useEffect(() => {
    const methodObj = wipeMethods.find(m => m.name === wipeMethod);
    if (methodObj) {
      setTotalPasses(methodObj.passes);
    }
  }, [wipeMethod]);

  const selectDrive = (drive) => {
    if (drive.isSystem) return; // Prevent selection of C:\
    setSelectedDrive(drive);
  };

  const handleWipeClick = () => {
    if (!selectedDrive) return;
    setSimState("confirm1");
  };

  const confirmFirst = () => {
    setSimState("confirm2");
  };

  const cancelWipe = () => {
    setSimState("idle");
    setProgress(0);
    setLogs([]);
  };

  const generateCertId = () => {
    const chars = 'ABCDEF0123456789';
    let result = 'ZT-';
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const startWipe = () => {
    setSimState("wiping");
    setProgress(0);
    setCurrentPass(1);
    setStatusText("Initializing Wipe...");
    setLogs([
      "[INFO] ZeroTrace C++ Core Engine initialized.",
      "[INFO] Acquiring administrative elevation privileges...",
      `[INFO] Target acquired: ${selectedDrive.model || selectedDrive.label} (${selectedDrive.size})`,
      `[INFO] Dismounting filesystem volume on ${selectedDrive.letter || 'Disk'}:\\`,
      "[INFO] Locking volume handles to prevent third-party I/O..."
    ]);

    let currentProgress = 0;
    let pass = 1;
    const methodObj = wipeMethods.find(m => m.name === wipeMethod);
    const passes = methodObj ? methodObj.passes : 1;
    
    const interval = setInterval(() => {
      // Simulate progress
      currentProgress += (100 / (passes * 12)); // Increment progress speed depending on passes
      if (currentProgress > 100) currentProgress = 100;
      
      const ratio = currentProgress / 100;
      setProgress(ratio);

      // Speed fluctuation
      const baseSpeed = selectedDrive.model.includes("SSD") || selectedDrive.model.includes("NVMe") ? 420 : 130;
      const currentSpeed = (baseSpeed + (Math.random() * 40 - 20)).toFixed(1);
      setSpeed(currentSpeed);

      // Determine current pass based on progress
      const passCalculated = Math.min(passes, Math.floor(ratio * passes) + 1);
      if (passCalculated !== pass) {
        pass = passCalculated;
        setCurrentPass(pass);
        setLogs(prev => [
          ...prev,
          `[PASS] Commencing Pass ${pass}/${passes}...`,
          `[WRITE] Overwriting blocks using ${pass % 2 === 0 ? '0xFF pattern' : 'random noise'}...`
        ]);
      }

      // Append random technical logs
      if (Math.random() > 0.6 && currentProgress < 100) {
        const hexAddress = '0x' + Math.floor(Math.random() * 16777215).toString(16).toUpperCase();
        setLogs(prev => [
          ...prev,
          `[WRITE] Block ${hexAddress} - verified overwrite at ${currentSpeed} MB/s`
        ]);
      }

      setStatusText(`Wiping (${wipeMethod}): Pass ${pass}/${passes} - ${Math.round(currentProgress)}%`);

      if (currentProgress >= 100) {
        clearInterval(interval);
        setStatusText("Generating certificate...");
        setLogs(prev => [
          ...prev,
          "[INFO] Overwrite phase completed.",
          "[INFO] Running entropy analysis verification...",
          "[VERIFY] 100% data destruction confirmed. 0.0000000 entropy value.",
          "[INFO] Unlocking volume handles...",
          "[INFO] Mounting clean raw volume...",
          "[SUCCESS] Target disk is fully sanitized.",
          "[INFO] Cryptographically signing PDF Certificate of Destruction..."
        ]);
        
        setTimeout(() => {
          setCertId(generateCertId());
          setSimState("complete");
        }, 1500);
      }
    }, 400);
  };

  const handleReset = () => {
    setSimState("idle");
    setSelectedDrive(null);
    setProgress(0);
    setLogs([]);
    setSpeed(0);
  };

  // Styles object
  const styles = {
    section: {
      padding: '100px 0',
      backgroundColor: '#050505',
      position: 'relative',
      overflow: 'hidden',
    },
    headerArea: {
      textAlign: 'center',
      marginBottom: '60px',
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: '700',
      marginBottom: '15px',
      background: 'linear-gradient(45deg, #fff, #888)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    subtitle: {
      fontSize: '1.1rem',
      color: 'var(--text-secondary)',
      maxWidth: '600px',
      margin: '0 auto',
    },
    glowBg: {
      position: 'absolute',
      width: '800px',
      height: '800px',
      background: 'radial-gradient(circle, rgba(0, 255, 157, 0.04) 0%, rgba(0, 0, 0, 0) 70%)',
      top: '20%',
      left: '50%',
      transform: 'translateX(-50%)',
      pointerEvents: 'none',
      zIndex: 1,
    },
    // Desktop window styling
    windowContainer: {
      position: 'relative',
      zIndex: 2,
      maxWidth: '900px',
      height: '580px',
      margin: '0 auto',
      background: '#181818',
      borderRadius: '12px',
      border: '1px solid #333',
      boxShadow: '0 20px 50px rgba(0,0,0,0.5), 0 0 30px rgba(0, 255, 157, 0.1)',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    titleBar: {
      height: '40px',
      background: '#202020',
      borderBottom: '1px solid #2d2d2d',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0 15px',
      userSelect: 'none',
    },
    titleText: {
      fontSize: '0.85rem',
      color: '#bbb',
      fontWeight: '600',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    windowIcon: {
      width: '12px',
      height: '12px',
      borderRadius: '50%',
      backgroundColor: 'var(--accent-primary)',
      display: 'inline-block',
      boxShadow: '0 0 8px var(--accent-primary)',
    },
    windowControls: {
      display: 'flex',
      gap: '12px',
    },
    winBtn: {
      width: '12px',
      height: '12px',
      borderRadius: '50%',
      display: 'inline-block',
    },
    appBody: {
      flex: 1,
      display: 'flex',
      overflow: 'hidden',
    },
    sidebar: {
      width: '200px',
      background: '#1d1d1d',
      borderRight: '1px solid #2d2d2d',
      display: 'flex',
      flexDirection: 'column',
      padding: '20px',
    },
    sidebarLogo: {
      fontSize: '1.25rem',
      fontWeight: '800',
      color: '#fff',
      marginBottom: '30px',
      letterSpacing: '-0.5px',
    },
    sidebarBtn: {
      padding: '10px 15px',
      fontSize: '0.9rem',
      fontWeight: '600',
      color: '#fff',
      backgroundColor: '#2d2d2d',
      border: '1px solid #3d3d3d',
      borderRadius: '6px',
      cursor: 'pointer',
      transition: 'all 0.2s',
      textAlign: 'center',
    },
    sidebarBtnActive: {
      backgroundColor: 'var(--accent-primary)',
      color: '#000',
      borderColor: 'var(--accent-primary)',
    },
    mainPanel: {
      flex: 1,
      padding: '30px',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
    },
    panelTitle: {
      fontSize: '1.4rem',
      fontWeight: '700',
      color: '#fff',
      marginBottom: '20px',
    },
    driveList: {
      flex: 1,
      background: '#121212',
      border: '1px solid #2d2d2d',
      borderRadius: '8px',
      padding: '10px',
      overflowY: 'auto',
      marginBottom: '20px',
      maxHeight: '180px',
    },
    driveRow: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '12px 15px',
      borderRadius: '6px',
      marginBottom: '8px',
      cursor: 'pointer',
      transition: 'all 0.2s',
      border: '1px solid transparent',
    },
    controlSection: {
      display: 'flex',
      flexDirection: 'column',
      gap: '15px',
    },
    dropdownLabel: {
      fontSize: '0.85rem',
      color: '#888',
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    select: {
      padding: '12px',
      background: '#1d1d1d',
      border: '1px solid #3d3d3d',
      borderRadius: '6px',
      color: '#fff',
      fontSize: '0.95rem',
      outline: 'none',
      cursor: 'pointer',
    },
    wipeBtn: {
      padding: '15px 0',
      background: 'var(--accent-danger)',
      color: '#fff',
      fontWeight: '700',
      fontSize: '1rem',
      borderRadius: '6px',
      cursor: 'pointer',
      textAlign: 'center',
      border: 'none',
      transition: 'all 0.2s',
      boxShadow: '0 4px 15px rgba(255, 77, 77, 0.2)',
    },
    // Wiping UI Layer
    wipingContainer: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
    },
    progressBarOuter: {
      width: '100%',
      height: '10px',
      background: '#222',
      borderRadius: '5px',
      overflow: 'hidden',
      marginBottom: '15px',
    },
    progressBarInner: {
      height: '100%',
      background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
      transition: 'width 0.2s ease-out',
    },
    consoleLogs: {
      flex: 1,
      background: '#090909',
      border: '1px solid #222',
      borderRadius: '8px',
      padding: '15px',
      fontFamily: '"Courier New", Courier, monospace',
      fontSize: '0.8rem',
      color: '#00ff66',
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
      maxHeight: '200px',
    },
    // Modal popup overlay
    modalOverlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      background: 'rgba(0,0,0,0.7)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10,
    },
    dialogBox: {
      width: '380px',
      background: '#202020',
      border: '1px solid #3d3d3d',
      borderRadius: '8px',
      boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
      overflow: 'hidden',
    },
    dialogHeader: {
      padding: '15px 20px',
      background: '#262626',
      borderBottom: '1px solid #2d2d2d',
      fontWeight: 'bold',
      color: '#fff',
      fontSize: '1rem',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    dialogBody: {
      padding: '25px 20px',
      color: '#ccc',
      fontSize: '0.95rem',
      lineHeight: '1.5',
    },
    dialogActions: {
      padding: '12px 20px',
      background: '#1c1c1c',
      display: 'flex',
      justifyContent: 'flex-end',
      gap: '10px',
      borderTop: '1px solid #2d2d2d',
    },
    dialogBtn: {
      padding: '8px 18px',
      borderRadius: '4px',
      fontSize: '0.85rem',
      fontWeight: '600',
      cursor: 'pointer',
      border: 'none',
    },
    // PDF Certificate Modal Styles
    certOverlay: {
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      background: 'rgba(5, 5, 5, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'flex-start', // Allows scrolling down
      justifyContent: 'center',
      zIndex: 2000,
      overflowY: 'auto', // Enable scrolling on smaller screens
      padding: '40px 0',
    },
    certCard: {
      width: '90%', // Responsive width
      maxWidth: '620px',
      background: '#ffffff',
      color: '#1a1a1a',
      borderRadius: '12px',
      padding: '40px 30px',
      boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
      position: 'relative',
      fontFamily: '"Georgia", serif',
      backgroundImage: 'radial-gradient(#f9f9f9 1px, transparent 0), radial-gradient(#f9f9f9 1px, transparent 0)',
      backgroundSize: '8px 8px',
      backgroundPosition: '0 0, 4px 4px',
      border: '8px double #d4af37', // Gold border for certificate feel
    },
    certHeader: {
      textAlign: 'center',
      borderBottom: '2px solid #1a1a1a',
      paddingBottom: '20px',
      marginBottom: '25px',
    },
    certTitle: {
      fontSize: '2rem',
      fontWeight: 'bold',
      letterSpacing: '1px',
      color: '#111',
      fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
      textTransform: 'uppercase',
    },
    certSubtitle: {
      fontSize: '0.85rem',
      color: '#666',
      marginTop: '5px',
      fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
      letterSpacing: '2px',
    },
    certTable: {
      width: '100%',
      borderCollapse: 'collapse',
      marginBottom: '25px',
      fontSize: '0.9rem',
    },
    certTdLabel: {
      padding: '8px 10px',
      fontWeight: 'bold',
      color: '#444',
      borderBottom: '1px solid #eee',
      width: '35%',
    },
    certTdValue: {
      padding: '8px 10px',
      color: '#222',
      borderBottom: '1px solid #eee',
      fontFamily: 'monospace',
    },
    certFooter: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: '30px',
      paddingTop: '20px',
      borderTop: '1px solid #eee',
    },
    certSeal: {
      border: '2px dashed #0088cc',
      color: '#0088cc',
      padding: '8px 15px',
      fontWeight: 'bold',
      borderRadius: '4px',
      fontSize: '0.75rem',
      textTransform: 'uppercase',
      letterSpacing: '1px',
      transform: 'rotate(-5deg)',
    },
    certSignature: {
      textAlign: 'center',
    },
    certSigLine: {
      width: '150px',
      borderBottom: '1px solid #1a1a1a',
      marginBottom: '5px',
    },
    certCloseBtn: {
      position: 'absolute',
      top: '15px', // Placed inside card for better visibility
      right: '15px',
      background: 'transparent',
      color: '#888', // Subtle color on white card
      fontSize: '1.8rem',
      border: 'none',
      cursor: 'pointer',
      lineHeight: '1',
      transition: 'color 0.2s',
    }
  };

  return (
    <section style={styles.section}>
      <div style={styles.glowBg}></div>
      <div className="container">
        
        <div style={styles.headerArea}>
          <h2 style={styles.title}>See ZeroTrace in Action</h2>
          <p style={styles.subtitle}>
            Interactive Web Demo — Test drive our low-level Windows Desktop interface safely inside your browser. No physical drives will be harmed.
          </p>
        </div>

        {/* Mock Windows Desktop Application */}
        <div style={styles.windowContainer}>
          
          {/* Title Bar */}
          <div style={styles.titleBar}>
            <div style={styles.titleText}>
              <span style={styles.windowIcon}></span>
              ZeroTrace - Secure Data Wiper
            </div>
            <div style={styles.windowControls}>
              <span style={{...styles.winBtn, backgroundColor: '#ffbd2e'}}></span>
              <span style={{...styles.winBtn, backgroundColor: '#27c93f'}}></span>
              <span style={{...styles.winBtn, backgroundColor: '#ff5f56', cursor: 'pointer'}} onClick={cancelWipe}></span>
            </div>
          </div>

          <div style={styles.appBody}>
            {/* Left Sidebar */}
            <div style={styles.sidebar}>
              <div style={styles.sidebarLogo}>
                Zero<span style={{color: 'var(--accent-primary)'}}>Trace</span>
              </div>
              <button 
                style={{
                  ...styles.sidebarBtn, 
                  ...(simState === 'idle' || simState === 'driveSelected' ? styles.sidebarBtnActive : {})
                }}
                disabled={simState === 'wiping'}
                onClick={handleReset}
              >
                Refresh Drives
              </button>
              
              <div style={{marginTop: 'auto', fontSize: '0.75rem', color: '#666', textAlign: 'center'}}>
                v1.3.0 Engine
              </div>
            </div>

            {/* Right Main Panel */}
            <div style={styles.mainPanel}>
              
              {/* Idle or drive selected layout */}
              {(simState === 'idle' || simState === 'driveSelected' || simState === 'confirm1' || simState === 'confirm2') && (
                <>
                  <h3 style={styles.panelTitle}>
                    {selectedDrive ? `Selected: ${selectedDrive.letter}:\\ - ${selectedDrive.label}` : "Select Drive to Wipe"}
                  </h3>
                  
                  {/* CTkScrollableFrame equivalent */}
                  <div style={styles.driveList}>
                    {mockDrives.map(drive => {
                      const isSelected = selectedDrive?.id === drive.id;
                      return (
                        <div 
                          key={drive.id}
                          onClick={() => selectDrive(drive)}
                          style={{
                            ...styles.driveRow,
                            backgroundColor: drive.isSystem ? '#222' : isSelected ? 'rgba(0, 255, 157, 0.1)' : '#1a1a1a',
                            borderColor: isSelected ? 'var(--accent-primary)' : '#2d2d2d',
                            cursor: drive.isSystem ? 'not-allowed' : 'pointer',
                            opacity: drive.isSystem ? 0.4 : 1,
                          }}
                        >
                          <div style={{fontWeight: '600', color: drive.isSystem ? '#666' : '#fff'}}>
                            {drive.letter}:\\ - {drive.label} ({drive.size})
                            {drive.isSystem && " [SYSTEM - PROTECTED]"}
                          </div>
                          {!drive.isSystem && (
                            <div style={{fontSize: '0.8rem', color: isSelected ? 'var(--accent-primary)' : '#888'}}>
                              {drive.model}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  <div style={styles.controlSection}>
                    <div style={{display: 'flex', flexDirection: 'column', gap: '5px'}}>
                      <span style={styles.dropdownLabel}>Wiping Method:</span>
                      <select 
                        style={styles.select} 
                        value={wipeMethod} 
                        onChange={(e) => setWipeMethod(e.target.value)}
                        disabled={simState === 'wiping'}
                      >
                        {wipeMethods.map((m, idx) => (
                          <option key={idx} value={m.name}>{m.name} ({m.passes} {m.passes === 1 ? 'Pass' : 'Passes'})</option>
                        ))}
                      </select>
                      <span style={{fontSize: '0.8rem', color: '#666', fontStyle: 'italic', marginTop: '2px'}}>
                        {wipeMethods.find(m => m.name === wipeMethod)?.desc}
                      </span>
                    </div>

                    <button 
                      onClick={handleWipeClick}
                      disabled={!selectedDrive}
                      style={{
                        ...styles.wipeBtn,
                        opacity: selectedDrive ? 1 : 0.4,
                        cursor: selectedDrive ? 'pointer' : 'not-allowed',
                        transform: selectedDrive ? 'none' : 'none'
                      }}
                    >
                      WIPE SELECTED DRIVE
                    </button>
                  </div>
                </>
              )}

              {/* Wiping Progress Layout */}
              {(simState === 'wiping' || simState === 'complete') && (
                <div style={styles.wipingContainer}>
                  <h3 style={{...styles.panelTitle, marginBottom: '5px'}}>
                    Wiping physical blocks...
                  </h3>
                  <div style={{fontSize: '0.85rem', color: '#888', marginBottom: '20px', display: 'flex', justifyContent: 'space-between'}}>
                    <span>Target: {selectedDrive?.letter}:\\ - {selectedDrive?.label} ({selectedDrive?.size})</span>
                    {simState === 'wiping' && <span style={{color: 'var(--accent-secondary)', fontWeight: 'bold'}}>{speed} MB/s</span>}
                  </div>

                  {/* Progress Bar */}
                  <div style={styles.progressBarOuter}>
                    <div style={{...styles.progressBarInner, width: `${progress * 100}%`}}></div>
                  </div>

                  <div style={{fontSize: '0.9rem', color: '#fff', fontWeight: '600', marginBottom: '15px'}}>
                    {statusText}
                  </div>

                  {/* Logs Console */}
                  <div ref={consoleRef} style={styles.consoleLogs}>
                    {logs.map((log, index) => (
                      <div key={index} style={{
                        color: log.startsWith('[SUCCESS]') ? 'var(--accent-primary)' : log.startsWith('[PASS]') ? '#00b8ff' : log.startsWith('[VERIFY]') ? '#bd00ff' : '#00ff66'
                      }}>
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confirm Popup 1 */}
              {simState === 'confirm1' && (
                <div style={styles.modalOverlay}>
                  <div style={styles.dialogBox}>
                    <div style={{...styles.dialogHeader, color: '#ff4d4d'}}>
                      ⚠️ WARNING
                    </div>
                    <div style={styles.dialogBody}>
                      PERMANENTLY ERASE ALL DATA ON:<br/><br/>
                      <strong>{selectedDrive.letter}:\\ - {selectedDrive.label} ({selectedDrive.size})</strong><br/>
                      Model: {selectedDrive.model}<br/>
                      Method: {wipeMethod}<br/><br/>
                      This cannot be undone. Are you sure?
                    </div>
                    <div style={styles.dialogActions}>
                      <button 
                        style={{...styles.dialogBtn, backgroundColor: '#333', color: '#fff'}} 
                        onClick={cancelWipe}
                      >
                        No
                      </button>
                      <button 
                        style={{...styles.dialogBtn, backgroundColor: 'var(--accent-danger)', color: '#fff'}} 
                        onClick={confirmFirst}
                      >
                        Yes
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Confirm Popup 2 */}
              {simState === 'confirm2' && (
                <div style={styles.modalOverlay}>
                  <div style={styles.dialogBox}>
                    <div style={{...styles.dialogHeader, color: '#ff4d4d'}}>
                      ⚠️ FINAL WARNING
                    </div>
                    <div style={styles.dialogBody}>
                      This is your last chance. All partition maps, file tables, and recovery sectors will be completely randomized.<br/><br/>
                      Do you absolutely wish to proceed?
                    </div>
                    <div style={styles.dialogActions}>
                      <button 
                        style={{...styles.dialogBtn, backgroundColor: '#333', color: '#fff'}} 
                        onClick={cancelWipe}
                      >
                        Abort
                      </button>
                      <button 
                        style={{...styles.dialogBtn, backgroundColor: 'var(--accent-danger)', color: '#fff'}} 
                        onClick={startWipe}
                      >
                        Proceed
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Success CustomTkinter popup */}
              {simState === 'complete' && (
                <div style={styles.modalOverlay}>
                  <div style={{...styles.dialogBox, width: '420px', textAlign: 'center'}}>
                    <div style={{fontSize: '3rem', paddingTop: '20px'}}>✅</div>
                    <h4 style={{fontSize: '1.25rem', fontWeight: 'bold', color: '#fff', margin: '10px 0'}}>
                      Drive Wiped Successfully!
                    </h4>
                    <div style={{padding: '10px 20px', fontSize: '0.9rem', color: '#aaa'}}>
                      Method: {wipeMethod}<br/>
                      Certificate file generated at:<br/>
                      <input 
                        type="text" 
                        readOnly 
                        value={`C:\\Users\\Admin\\ZeroTrace\\certs\\${certId}_cert.pdf`}
                        style={{
                          width: '100%', 
                          background: '#121212', 
                          border: '1px solid #333', 
                          color: 'var(--accent-primary)',
                          padding: '6px', 
                          borderRadius: '4px',
                          marginTop: '8px', 
                          textAlign: 'center', 
                          fontSize: '0.75rem',
                          fontFamily: 'monospace',
                          outline: 'none'
                        }}
                      />
                    </div>
                    <div style={{
                      padding: '20px', 
                      display: 'flex', 
                      justifyContent: 'center', 
                      gap: '15px',
                      background: '#1a1a1a',
                      marginTop: '15px',
                      borderTop: '1px solid #2d2d2d'
                    }}>
                      <button 
                        style={{
                          ...styles.dialogBtn, 
                          backgroundColor: 'var(--accent-primary)', 
                          color: '#000', 
                          width: '120px'
                        }} 
                        onClick={() => setSimState("viewingCert")}
                      >
                        Open PDF
                      </button>
                      <button 
                        style={{
                          ...styles.dialogBtn, 
                          backgroundColor: '#333', 
                          color: '#fff', 
                          width: '120px'
                        }} 
                        onClick={handleReset}
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>

      </div>

      {/* PDF Certificate Viewer Modal Overlay */}
      {simState === "viewingCert" && (
        <div style={styles.certOverlay}>
          <div style={styles.certCard}>
            <button style={styles.certCloseBtn} onClick={handleReset}>×</button>
            
            <div style={styles.certHeader}>
              <h2 style={styles.certTitle}>Certificate of Sanitization</h2>
              <div style={styles.certSubtitle}>ZeroTrace Cryptographic Verification Document</div>
            </div>

            <table style={styles.certTable}>
              <tbody>
                <tr>
                  <td style={styles.certTdLabel}>Certificate ID</td>
                  <td style={styles.certTdValue}>{certId}</td>
                </tr>
                <tr>
                  <td style={styles.certTdLabel}>Sanitized Target</td>
                  <td style={styles.certTdValue}>{selectedDrive?.model || 'Generic Disk'} ({selectedDrive?.size})</td>
                </tr>
                <tr>
                  <td style={styles.certTdLabel}>Logical Volume</td>
                  <td style={styles.certTdValue}>{selectedDrive?.letter}:\\ ("{selectedDrive?.label}")</td>
                </tr>
                <tr>
                  <td style={styles.certTdLabel}>Sanitization Standard</td>
                  <td style={styles.certTdValue}>{wipeMethod} ({totalPasses} {totalPasses === 1 ? 'Pass' : 'Passes'})</td>
                </tr>
                <tr>
                  <td style={styles.certTdLabel}>Entropy Check</td>
                  <td style={styles.certTdValue}>0.000000 (Pass - Verified 100% Null/Randomized)</td>
                </tr>
                <tr>
                  <td style={styles.certTdLabel}>Hardware Engine</td>
                  <td style={styles.certTdValue}>ZeroTrace C++ Core (wiper_core.dll v1.3.0)</td>
                </tr>
                <tr>
                  <td style={styles.certTdLabel}>Verification Hash</td>
                  <td style={{...styles.certTdValue, fontSize: '0.75rem', wordBreak: 'break-all'}}>
                    {btoa(certId + wipeMethod + selectedDrive?.size).substring(0, 48).toLowerCase()}
                  </td>
                </tr>
                <tr>
                  <td style={styles.certTdLabel}>Date of Execution</td>
                  <td style={styles.certTdValue}>{new Date().toUTCString()}</td>
                </tr>
              </tbody>
            </table>

            <div style={styles.certFooter}>
              <div style={styles.certSeal}>
                NIST SP 800-88<br/>
                Compliant
              </div>
              <div style={styles.certSignature}>
                <div style={styles.certSigLine}></div>
                <div style={{fontSize: '0.75rem', color: '#666', textTransform: 'uppercase', letterSpacing: '1px'}}>
                  ZeroTrace Engine Signature
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </section>
  );
};

export default WipeSimulator;
