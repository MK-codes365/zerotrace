"""
ZeroTrace Disk & Media Manager
Comprehensive device detection via WMI, Windows Storage APIs, and Win32.
Detects physical drives, partitions, media types (HDD vs SSD vs USB vs SD),
bus interfaces (NVMe, SATA, USB), and guards system drive safety.
"""

import os
import subprocess
from typing import List, Dict, Any

try:
    import wmi
    HAS_WMI = True
except ImportError:
    HAS_WMI = False


def get_system_drive_letter() -> str:
    return os.environ.get("SystemDrive", "C:").replace(":", "")


def format_size(bytes_size: int) -> str:
    """Format bytes into readable string."""
    b = float(bytes_size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024.0:
            return f"{b:.2f} {unit}"
        b /= 1024.0
    return f"{b:.2f} PB"


def is_system_drive(device_id: str) -> bool:
    sys_letter = get_system_drive_letter()
    u = device_id.upper()
    return f"{sys_letter}:" in u or "PHYSICALDRIVE0" in u


def list_volumes() -> List[Dict[str, Any]]:
    """List all mounted logical volumes with filesystem and capacity."""
    volumes = []
    sys_letter = get_system_drive_letter()

    if HAS_WMI:
        try:
            c = wmi.WMI()
            for logical_disk in c.Win32_LogicalDisk():
                drive_type = logical_disk.DriveType
                # 2: Removable, 3: Fixed, 4: Network, 5: CD
                if drive_type in (2, 3):
                    letter = logical_disk.DeviceID.replace(":", "")
                    device_id = f"\\\\.\\{letter}:"
                    label = logical_disk.VolumeName or ("Removable Disk" if drive_type == 2 else "Local Disk")
                    size = int(logical_disk.Size) if logical_disk.Size else 0
                    free_space = int(logical_disk.FreeSpace) if logical_disk.FreeSpace else 0
                    is_sys = (letter.upper() == sys_letter.upper())

                    media_type = "USB / Removable" if drive_type == 2 else "Fixed Volume"

                    volumes.append({
                        "device_id": device_id,
                        "label": label,
                        "letter": letter,
                        "size": size,
                        "free_space": free_space,
                        "filesystem": logical_disk.FileSystem or "NTFS",
                        "is_system": is_sys,
                        "media_type": media_type,
                        "type": "volume",
                        "display_name": f"[{letter}:] {label} ({format_size(size)}) - {logical_disk.FileSystem or 'NTFS'}",
                    })
            if volumes:
                return volumes
        except Exception:
            pass

    # Fallback if WMI fails or drives missing
    for letter in ["C", "D", "E", "F"]:
        path = f"{letter}:\\"
        if os.path.exists(path):
            try:
                import ctypes
                free_bytes = ctypes.c_ulonglong()
                total_bytes = ctypes.c_ulonglong()
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    path, None, ctypes.byref(total_bytes), ctypes.byref(free_bytes)
                )
                size = total_bytes.value
                free = free_bytes.value
            except Exception:
                size = 100 * 1024 * 1024 * 1024
                free = 50 * 1024 * 1024 * 1024

            is_sys = (letter.upper() == sys_letter.upper())
            volumes.append({
                "device_id": f"\\\\.\\{letter}:",
                "label": f"Local Disk ({letter}:)",
                "letter": letter,
                "size": size,
                "free_space": free,
                "filesystem": "NTFS",
                "is_system": is_sys,
                "media_type": "Fixed Volume",
                "type": "volume",
                "display_name": f"[{letter}:] Local Disk ({format_size(size)})",
            })

    return volumes


def list_physical_drives() -> List[Dict[str, Any]]:
    """List physical storage devices with SSD / HDD / USB classification."""
    drives = []
    sys_letter = get_system_drive_letter()

    if HAS_WMI:
        try:
            c = wmi.WMI()
            for pdisk in c.Win32_DiskDrive():
                device_id = pdisk.DeviceID
                model = pdisk.Model or "Physical Storage Device"
                size = int(pdisk.Size) if pdisk.Size else 0
                interface = pdisk.InterfaceType or "SCSI"
                media = pdisk.MediaType or "Fixed hard disk media"

                # Detect if drive hosts system partition
                is_sys = False
                try:
                    for partition in pdisk.associators("Win32_DiskDriveToDiskPartition"):
                        for logical in partition.associators("Win32_LogicalDiskToPartition"):
                            if logical.DeviceID.startswith(sys_letter):
                                is_sys = True
                                break
                except Exception:
                    if "0" in device_id:
                        is_sys = True

                # Media classification: NVMe / SSD vs Rotational HDD vs USB
                u_model = model.upper()
                u_media = media.upper()
                if "NVME" in u_model or "SSD" in u_model or "NVME" in interface.upper():
                    media_type = "SSD (NVMe/Solid-State)"
                elif "USB" in interface.upper() or "REMOVABLE" in u_media:
                    media_type = "USB Removable Drive"
                elif "SD" in u_model:
                    media_type = "SD Card"
                else:
                    media_type = "HDD (Magnetic Rotational)"

                drives.append({
                    "device_id": device_id,
                    "model": model,
                    "size": size,
                    "interface": interface,
                    "media_type": media_type,
                    "is_system": is_sys,
                    "serial": pdisk.SerialNumber.strip() if pdisk.SerialNumber else "N/A",
                    "type": "physical",
                    "display_name": f"{model} ({format_size(size)}) [{media_type}]",
                })
        except Exception as e:
            print(f"[DISK_MANAGER] Error reading physical drives: {e}")

    return drives


def list_all_wipeable_targets() -> List[Dict[str, Any]]:
    """Return unified list of wipeable targets (both volumes and physical disks)."""
    return list_volumes() + list_physical_drives()
