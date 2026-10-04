/**
 * Offline Recovery Advisor Service
 * Local rule matcher for air-gapped forensic environments.
 */

export interface RecoveryRequest {
  scenario: string;
  driveType?: string;
  fileSystem?: string;
}

export interface RecoveryResponse {
  recommendation: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  forensicStandard?: string;
}

export class OfflineAdvisor {
  public static matchRule(request: RecoveryRequest): RecoveryResponse {
    const scenario = (request.scenario || '').toLowerCase();
    const driveType = (request.driveType || '').toLowerCase();

    // Rule 1: SSD Deletion (TRIM risk)
    if (scenario.includes('delete') && driveType.includes('ssd')) {
      return {
        recommendation: "WARNING: SSD uses TRIM operations. Blocks may be permanently zeroed quickly. Isolate power immediately and conduct hardware-level raw extraction.",
        riskLevel: "CRITICAL",
        forensicStandard: "NIST SP 800-88 Rev 1 Guidelines"
      };
    }

    // Rule 2: Formatted Disk
    if (scenario.includes('format')) {
      return {
        recommendation: "Disk structure altered. Execute raw carving techniques. Recommendation: Use Scalpel / Foremost to parse raw headers and signatures bypassing file system maps.",
        riskLevel: "HIGH",
        forensicStandard: "ISO/IEC 27037 Chain of Custody Standards"
      };
    }

    // Default Fallback
    return {
      recommendation: "Standard storage anomaly detected. Preserve drive state, block write access with a hardware write-blocker, and clone bit-stream image (DD/E01).",
      riskLevel: "MEDIUM",
      forensicStandard: "NIST SP 800-88 Reference"
    };
  }
}
