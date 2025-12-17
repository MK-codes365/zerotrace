import wmi

def get_system_drive_letter():
    """
    Get the system drive letter (usually C:)
    """
    import os
    return os.environ.get('SystemDrive', 'C:').replace(':', '')

def format_size(bytes_size):
    """
    Convert bytes to human-readable format
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def list_volumes():
    """
    List all logical volumes (partitions with drive letters)
    Returns list of dicts with device_id, label, size, letter, is_system
    """
    c = wmi.WMI()
    volumes = []
    system_drive = get_system_drive_letter()
    
    for logical_disk in c.Win32_LogicalDisk(DriveType=3):  # DriveType=3 = Local Disk
        letter = logical_disk.DeviceID.replace(':', '')  # e.g., "C", "D", "F"
        device_id = f"\\\\.\\{letter}:"  # e.g., \\.\C:, \\.\F:
        label = logical_disk.VolumeName or "Local Disk"
        size = int(logical_disk.Size) if logical_disk.Size else 0
        is_system = (letter == system_drive)
        
        volumes.append({
            'device_id': device_id,
            'label': label,
            'letter': letter,
            'size': size,
            'is_system': is_system,
            'type': 'volume'
        })
    
    return volumes

def list_all_wipeable_targets():
    """
    List all wipeable targets (volumes/partitions)
    Returns list of volumes (partitions are safer than physical drives)
    """
    return list_volumes()

# Legacy function for compatibility
def list_physical_drives():
    """
    List all physical drives (entire disks)
    NOTE: Physical drive wiping disabled by default for safety
    """
    c = wmi.WMI()
    drives = []
    system_drive = get_system_drive_letter()
    
    for physical_disk in c.Win32_DiskDrive():
        device_id = physical_disk.DeviceID
        model = physical_disk.Model or "Unknown"
        size = int(physical_disk.Size) if physical_disk.Size else 0
        
        # Check if this is the system disk
        is_system = False
        for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                if logical_disk.DeviceID.startswith(system_drive):
                    is_system = True
                    break
        
        drives.append({
            'device_id': device_id,
            'model': model,
            'size': size,
            'is_system': is_system,
            'type': 'physical'
        })
    
    return drives

def is_system_drive(device_id):
    """
    Legacy compatibility function
    """
    return 'C:' in device_id or 'PHYSICALDRIVE0' in device_id
