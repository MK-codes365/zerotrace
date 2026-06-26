import wmi

def get_system_drive_letter():
    import os
    return os.environ.get('SystemDrive', 'C:').replace(':', '')

def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def list_volumes():
    c = wmi.WMI()
    volumes = []
    system_drive = get_system_drive_letter()
    
    for logical_disk in c.Win32_LogicalDisk(DriveType=3):  
        letter = logical_disk.DeviceID.replace(':', '')  
        device_id = f"\\\\.\\{letter}:"  
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
    return list_volumes() + list_physical_drives()

def list_physical_drives():
    c = wmi.WMI()
    drives = []
    system_drive = get_system_drive_letter()
    
    for physical_disk in c.Win32_DiskDrive():
        device_id = physical_disk.DeviceID
        model = physical_disk.Model or "Unknown"
        size = int(physical_disk.Size) if physical_disk.Size else 0
        
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
    return 'C:' in device_id or 'PHYSICALDRIVE0' in device_id
