import os
import random
import time
import ctypes
from ctypes import wintypes, c_char_p, c_int, c_uint64, c_double, CFUNCTYPE, POINTER

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = -1

ProgressCallbackType = CFUNCTYPE(None, c_double, c_uint64, c_uint64, c_int, c_int)

try:
    dll_path = os.path.join(os.path.dirname(__file__), "wiper_core.dll")
    wiper_dll = ctypes.CDLL(dll_path)
    
    wiper_dll.wipe_drive.argtypes = [c_char_p, c_int, ProgressCallbackType]
    wiper_dll.wipe_drive.restype = c_int
    
    wiper_dll.verify_drive.argtypes = [c_char_p, c_int, c_int]
    wiper_dll.verify_drive.restype = ctypes.c_bool
    
    wiper_dll.cancel_wipe.argtypes = []
    wiper_dll.cancel_wipe.restype = None
    
    NATIVE_DLL_AVAILABLE = True
    print("[INFO] Using C++ Native Core (wiper_core.dll)")
except:
    NATIVE_DLL_AVAILABLE = False
    print("[INFO] C++ DLL not found, using Python fallback")

METHOD_MAP = {
    "NIST 800-88 Clear": 0,
    "NIST 800-88-2 Purge": 1,
    "DoD 5220.22-M (3-Pass)": 2,
    "DoD 5220.22-M ECE (7-Pass)": 3,
    "Peter Gutmann (35-Pass)": 4,
}

class NativeCppWiper:
    def __init__(self, device_id, buffer_size=4*1024*1024):
        self.device_id = device_id
        self.buffer_size = buffer_size
        self.is_running = False

    def get_wipe_methods(self):
        return METHOD_MAP

    def run_wipe(self, method_name, progress_callback=None):
        self.is_running = True
        method_id = METHOD_MAP.get(method_name, 0)
        
        if ':\\' in self.device_id: 
            print(f"[INFO] Attempting to dismount volume {self.device_id}...")
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            handle = kernel32.CreateFileW(
                self.device_id,
                0xC0000000, 
                3,  
                None,
                3,  
                0,
                None
            )
            
            if handle != -1:
                bytes_returned = ctypes.c_ulong()
                
                kernel32.DeviceIoControl(handle, 0x00090018, None, 0, None, 0, ctypes.byref(bytes_returned), None)
                print(f"[INFO] Volume locked")
                
                result = kernel32.DeviceIoControl(handle, 0x00090020, None, 0, None, 0, ctypes.byref(bytes_returned), None)
                if result:
                    print(f"[INFO] Volume dismounted successfully")
                else:
                    print(f"[WARNING] Could not dismount volume, Error: {ctypes.GetLastError()}")
                
                kernel32.CloseHandle(handle)
            else:
                print(f"[WARNING] Could not open volume for dismount, Error: {ctypes.GetLastError()}")
        
        @ProgressCallbackType
        def callback_wrapper(progress, total, current, pass_num, total_passes):
            if progress_callback:
                progress_callback(progress, total, current, pass_num, total_passes)
        
        print(f"[DEBUG] Calling C++ DLL with device: {self.device_id}, method: {method_id}")
        result = wiper_dll.wipe_drive(
            self.device_id.encode('utf-8'),
            method_id,
            callback_wrapper
        )
        
        print(f"[DEBUG] C++ DLL returned: {result}")
        if result != 0:
            print(f"[ERROR] C++ Wiper failed with Windows error code: {result}")
            print(f"[ERROR] Common causes:")
            print(f"  - Error 5 (Access Denied): Need Administrator rights OR close programs using this drive")
            print(f"  - Error 32 (Sharing Violation): Drive is in use by another process")
            print(f"  - Error 87 (Invalid Parameter): Drive path incorrect")
            return False
        
        return True

    def stop(self):
        self.is_running = False
        wiper_dll.cancel_wipe()

    def verify_wipe(self, method_name, num_checks=10):
        method_id = METHOD_MAP.get(method_name, 0)
        return wiper_dll.verify_drive(self.device_id.encode('utf-8'), method_id, num_checks)


class CtypesWiper:
    def __init__(self, device_id, buffer_size=1024*1024):
        self.device_id = device_id
        self.buffer_size = buffer_size
        self.is_running = False
        self.kernel32 = ctypes.windll.kernel32

    def get_wipe_methods(self):
        return METHOD_MAP

    def _open_drive(self):
        handle = self.kernel32.CreateFileW(
            self.device_id,
            GENERIC_READ | GENERIC_WRITE,
            0,
            None,
            OPEN_EXISTING,
            0,
            None
        )
        
        if handle == INVALID_HANDLE_VALUE:
            raise Exception(f"Failed to open drive {self.device_id}. Error: {ctypes.GetLastError()}")
            
        return handle

    def _get_size(self, handle):
        new_pos = ctypes.c_longlong(0)
        success = self.kernel32.SetFilePointerEx(handle, ctypes.c_longlong(0), ctypes.byref(new_pos), 2)
        if not success:
            return 0
        size = new_pos.value
        self.kernel32.SetFilePointerEx(handle, ctypes.c_longlong(0), None, 0)
        return size

    def _wipe_pass(self, handle, total_size, pattern=None, pass_num=1, total_passes=1, progress_callback=None):
        self.kernel32.SetFilePointerEx(handle, ctypes.c_longlong(0), None, 0)
        written_total = 0
        
        if pattern:
             if len(pattern) == 1:
                 c_buffer = ctypes.create_string_buffer(self.buffer_size)
                 ctypes.memset(c_buffer, ord(pattern), self.buffer_size)
             else:
                 full_pat = (pattern * (self.buffer_size // len(pattern) + 1))[:self.buffer_size]
                 c_buffer = ctypes.create_string_buffer(full_pat)
        else:
            c_buffer = None

        while written_total < total_size and self.is_running:
            remaining = total_size - written_total
            current_chunk = min(remaining, self.buffer_size)
            
            if c_buffer:
                success = self.kernel32.WriteFile(handle, c_buffer, current_chunk, None, None)
            else:
                rand_bytes = os.urandom(current_chunk)
                c_rand = (ctypes.c_char * len(rand_bytes)).from_buffer_copy(rand_bytes)
                success = self.kernel32.WriteFile(handle, c_rand, current_chunk, None, None)

            if not success:
                return False

            written_total += current_chunk
            
            if progress_callback:
                base_progress = (pass_num - 1) / total_passes
                pass_progress = (written_total / total_size) / total_passes
                total_progress = base_progress + pass_progress
                progress_callback(total_progress, total_size, written_total, pass_num, total_passes)
        
        self.kernel32.FlushFileBuffers(handle)
        return self.is_running

    def run_wipe(self, method_name, progress_callback=None):
        self.is_running = True
        method_id = METHOD_MAP.get(method_name, 0)
        
        handle = INVALID_HANDLE_VALUE
        try:
            handle = self._open_drive()
            total_size = self._get_size(handle)
            if total_size == 0:
                raise Exception("Could not determine drive size.")
            
            if method_id == 0: 
                return self._wipe_pass(handle, total_size, b'\x00', 1, 1, progress_callback)
            elif method_id == 1: 
                return self._wipe_pass(handle, total_size, None, 1, 1, progress_callback)
            elif method_id == 2: 
                if not self._wipe_pass(handle, total_size, b'\x00', 1, 3, progress_callback): return False
                if not self._wipe_pass(handle, total_size, b'\xFF', 2, 3, progress_callback): return False
                return self._wipe_pass(handle, total_size, None, 3, 3, progress_callback)
            elif method_id == 3: 
                patterns = [b'\x00', b'\xFF', None, b'\x00', b'\x00', b'\xFF', None]
                for i, p in enumerate(patterns):
                    if not self._wipe_pass(handle, total_size, p, i+1, 7, progress_callback): return False
                return True
            elif method_id == 4: 
                total = 35
                for i in range(1, 5):
                    if not self._wipe_pass(handle, total_size, None, i, total, progress_callback): return False
                for i in range(5, 32):
                    pat = b'\x55' if i % 2 == 0 else b'\xAA'
                    if not self._wipe_pass(handle, total_size, pat, i, total, progress_callback): return False
                for i in range(32, 36):
                    if not self._wipe_pass(handle, total_size, None, i, total, progress_callback): return False
                return True
            
        except Exception as e:
            print(f"Wipe Error: {e}")
            return False
        finally:
            if handle != INVALID_HANDLE_VALUE:
                self.kernel32.CloseHandle(handle)

    def stop(self):
        self.is_running = False

    def verify_wipe(self, method_name, num_checks=10):
        method_id = METHOD_MAP.get(method_name, 0)
        handle = INVALID_HANDLE_VALUE
        try:
            handle = self.kernel32.CreateFileW(
                self.device_id, GENERIC_READ, 1|2, None, OPEN_EXISTING, 0, None)
            
            if handle == INVALID_HANDLE_VALUE: return False
            total_size = self._get_size(handle)
            if total_size < 512: return False
            
            buffer = ctypes.create_string_buffer(512)
            bytes_read = wintypes.DWORD(0)
            
            for _ in range(num_checks):
                offset = random.randint(0, total_size - 512)
                self.kernel32.SetFilePointerEx(handle, ctypes.c_longlong(offset), None, 0)
                success = self.kernel32.ReadFile(handle, buffer, 512, ctypes.byref(bytes_read), None)
                if not success or bytes_read.value != 512:
                    self.kernel32.CloseHandle(handle)
                    return False
                
                raw_bytes = buffer.raw[:512]
                if method_id == 0:
                    # NIST Clear: must be all zeros
                    if any(b != 0 for b in raw_bytes):
                        self.kernel32.CloseHandle(handle)
                        return False
                else:
                    # Other methods: must not be all zeros and not all 0xFF
                    if all(b == 0 for b in raw_bytes) or all(b == 255 for b in raw_bytes):
                        self.kernel32.CloseHandle(handle)
                        return False
            
            self.kernel32.CloseHandle(handle)
            return True
        except Exception as e:
            print(f"Verification Error: {e}")
            if handle != INVALID_HANDLE_VALUE: self.kernel32.CloseHandle(handle)
            return False


def Wiper(device_id, buffer_size=4*1024*1024):
    if NATIVE_DLL_AVAILABLE:
        return NativeCppWiper(device_id, buffer_size)
    else:
        return CtypesWiper(device_id, buffer_size)
