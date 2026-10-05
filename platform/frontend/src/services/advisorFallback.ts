export interface FallbackAdvisorResponse {
  answer: string;
  warnings: string[];
  riskLevel?: 'LOW' | 'MEDIUM' | 'CRITICAL';
  actionType?: string;
}

/**
 * Clean local fallback advisor engine.
 * Ensures the ZeroTrace Recovery Advisor operates reliably even if the backend is offline.
 */
export function getLocalAdvisorAdvice(query: string): FallbackAdvisorResponse {
  const q = query.toLowerCase().trim();

  // 1. Accidental SSD Deletion
  if (
    (q.includes('ssd') && (q.includes('delet') || q.includes('trim') || q.includes('erase') || q.includes('lost'))) ||
    q.includes('accidental ssd deletion')
  ) {
    return {
      answer:
        '**Accidental SSD Deletion — Recommended Recovery Strategy**\n\n' +
        '1. **Cease all write operations immediately**: Power down or safely disconnect the drive. Background OS processes and garbage collection actively overwrite unallocated sectors.\n' +
        '2. **Avoid installing tools onto the affected drive**: Never install recovery utilities or save recovered files back onto the target SSD.\n' +
        '3. **Forensic Bitstream Imaging First**: Acquire a complete read-only RAW/E01 disk image using a write-blocker before any recovery analysis.\n' +
        '4. **Analysis on Image**: Perform all file carving and filesystem parsing exclusively on the acquired disk image.\n' +
        '5. **SSD TRIM Factor**: SSD TRIM commands communicate with wear-leveling controllers, which can cause deleted flash blocks to return zeroes. While recovery cannot be guaranteed due to TRIM determinism, carving un-TRIMmed pages or controller cache immediately gives the highest probability of recovery.',
      warnings: [
        'Stop writing new data to the SSD immediately.',
        'Do NOT install recovery software onto the affected SSD.',
        'Never recover files back onto the same device.',
        'SSD TRIM commands may have already purged sector metadata; successful recovery cannot be guaranteed.',
        'Always create a write-blocked forensic bitstream image before scanning.',
      ],
      riskLevel: 'MEDIUM',
      actionType: 'IMAGE_DISK',
    };
  }

  // 2. Formatted USB (FAT32)
  if (
    (q.includes('usb') || q.includes('flash') || q.includes('thumb') || q.includes('fat32') || q.includes('sd card')) &&
    (q.includes('format') || q.includes('quick format') || q.includes('formatted')) ||
    q.includes('formatted usb')
  ) {
    return {
      answer:
        '**Formatted USB (FAT32) — Recommended Recovery Strategy**\n\n' +
        '1. **Stop using the USB drive**: Do not format it again or copy any new files to the device.\n' +
        '2. **Forensic Image First**: Create a bitstream image (RAW/.dd/.img) using a write-blocker to preserve the current state.\n' +
        '3. **Filesystem-Aware Recovery**: Quick formatting FAT32 wipes the File Allocation Table and root directory cluster, but cluster data remains intact. Scan for residual directory entries and subfolder clusters.\n' +
        '4. **Signature-Based Deep Carving (Scalpel)**: If filesystem metadata is destroyed, utilize signature-based carving to extract contiguous and structured files based on headers and footers.\n' +
        '5. **External Destination**: Always save recovered artifacts to a completely separate target drive.',
      warnings: [
        'Stop using the USB drive immediately.',
        'Do NOT format the drive again.',
        'Create a forensic image first before running extraction tools.',
        'Always save all extracted files to a separate storage drive.',
      ],
      riskLevel: 'LOW',
      actionType: 'LAUNCH_CARVE',
    };
  }

  // 3. Corrupted RAW Partition
  if (
    q.includes('raw') ||
    q.includes('corrupt') ||
    q.includes('unallocated') ||
    q.includes('partition') ||
    q.includes('filesystem') ||
    q.includes('corrupted raw partition')
  ) {
    return {
      answer:
        '**Corrupted RAW Partition — Recommended Recovery Strategy**\n\n' +
        '1. **Do NOT format the RAW partition**: Ignore all OS prompts asking to format or initialize the disk.\n' +
        '2. **Do NOT initialize the disk if Windows prompts**: Initializing writes new partition tables (MBR/GPT) and wipes volume headers.\n' +
        '3. **Acquire a Forensic Image**: Capture a complete bitstream copy of the entire physical drive.\n' +
        '4. **Filesystem Reconstruction & Metadata Inspection**: Parse backup boot sectors (VBR), MFT mirrors, or Superblocks to reconstruct the logical volume.\n' +
        '5. **Signature-Based Carving Fallback**: If volume metadata is irreparably corrupted, run signature-based carving on the forensic image.',
      warnings: [
        'Do NOT format the RAW partition when prompted by the operating system.',
        'Do NOT initialize the disk if Windows disk management requests it.',
        'Acquire a complete raw bitstream image before any repair attempts.',
        'Work strictly from the forensic image whenever possible.',
      ],
      riskLevel: 'MEDIUM',
      actionType: 'IMAGE_DISK',
    };
  }

  // 4. Clicking Hard Drive
  if (
    q.includes('click') ||
    q.includes('grind') ||
    q.includes('noise') ||
    q.includes('sound') ||
    q.includes('dropping') ||
    q.includes('hardware') ||
    q.includes('head') ||
    q.includes('clicking hard drive')
  ) {
    return {
      answer:
        '**Clicking Hard Drive — Critical Physical Failure Alert**\n\n' +
        '1. **Power off the drive immediately**: Clicking sounds (the "click of death") indicate physical read/write head assembly failure, head-stack misalignment, or spindle motor damage.\n' +
        '2. **Stop repeatedly powering or accessing the drive**: Repeated attempts grind the head slider into magnetic platter surfaces, destroying data tracks permanently.\n' +
        '3. **Avoid aggressive filesystem repair tools**: Do NOT run CHKDSK, fsck, or automated software scanners against a physically dying drive.\n' +
        '4. **Prioritize Professional Data Recovery**: If the lost data is mission-critical or legally significant, send the drive to a certified ISO Class 5 cleanroom laboratory.\n' +
        '5. **Controlled Hardware Imaging Only**: If recovery is attempted in-house, use dedicated hardware imagers with bad-sector skipping and head-map disabling (e.g., PC-3000 or specialized ddrescue).\n\n' +
        '*Note: Physical drive failure can worsen rapidly with continued operation. Recovery cannot be guaranteed.*',
      warnings: [
        'CRITICAL: Power off the drive immediately. Physical failure worsens with every spin cycle.',
        'Stop repeatedly powering or accessing the disk.',
        'Avoid running aggressive filesystem repairs (e.g. CHKDSK) or continuous software scans.',
        'Prioritize professional cleanroom data recovery for critical evidence.',
        'ZeroTrace does not guarantee recovery from mechanically damaged storage units.',
      ],
      riskLevel: 'CRITICAL',
      actionType: 'IMAGE_DISK',
    };
  }

  // 5. Generic / Forensics general guidance
  return {
    answer:
      '**ZeroTrace Forensic Recovery Assessment**\n\n' +
      'To ensure the highest recovery integrity and legal admissibility, follow ZeroTrace standard operating procedures:\n\n' +
      '1. **Write-Block Protection**: Connect the source media through a hardware or software write-blocker.\n' +
      '2. **Bitstream Acquisition**: Generate a verified 1:1 bitstream forensic image (E01 or RAW dd) with cryptographic hashes (SHA-256 / MD5).\n' +
      '3. **Non-Destructive Carving**: Execute signature-based extraction (Scalpel) or Master File Table (MFT) scanning against the image file.\n' +
      '4. **Separate Destination**: Direct all carved outputs to an external sanitized storage volume.\n' +
      '5. **Audit Trail**: Record all actions to maintain a tamper-evident chain of custody.',
    warnings: [
      'Never execute write or repair operations directly on the original evidentiary media.',
      'Always work on a verified forensic duplicate image.',
      'Maintain continuous chain of custody documentation.',
    ],
    riskLevel: 'LOW',
    actionType: 'LAUNCH_CARVE',
  };
}
