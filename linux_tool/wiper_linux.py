import ctypes
import os
import sys
import argparse
import time

# Load the shared library
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libwiper.so")
try:
    wiper = ctypes.CDLL(lib_path)
except OSError:
    print(f"Error: Could not load {lib_path}. Run 'make' to compile the library first.")
    sys.exit(1)

# Define callback type
# void (*ProgressCallback)(double progress, uint64_t total, uint64_t current, int pass, int total_passes);
PROGRESS_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_double, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int, ctypes.c_int)

# Define argument types
wiper.wipe_drive.argtypes = [ctypes.c_char_p, ctypes.c_int, PROGRESS_CALLBACK]
wiper.wipe_drive.restype = ctypes.c_int

wiper.verify_drive.argtypes = [ctypes.c_char_p, ctypes.c_int]
wiper.verify_drive.restype = ctypes.c_int

wiper.cancel_wipe.argtypes = []
wiper.cancel_wipe.restype = None

# Methods map
METHODS = {
    "NIST_CLEAR": 0,
    "NIST_PURGE": 1,
    "DOD_3PASS": 2,
    "DOD_7PASS": 3,
    "GUTMANN": 4
}

def progress_handler(progress, total_bytes, current_bytes, pass_num, total_passes):
    bar_length = 40
    filled_length = int(bar_length * progress)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    
    percent = progress * 100
    
    # Calculate speed (simplistic)
    # real app would track time delta
    
    sys.stdout.write(f"\r[{bar}] {percent:.2f}% | Pass {pass_num}/{total_passes} | {current_bytes}/{total_bytes} bytes")
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="ZeroTrace Linux Wiper")
    parser.add_argument("device", help="Path to the device or file to wipe (e.g., /dev/sdb)")
    parser.add_argument("--method", choices=METHODS.keys(), default="NIST_CLEAR", help="Wiping method")
    parser.add_argument("--verify", type=int, default=0, help="Number of verification checks (random spots)")
    
    args = parser.parse_args()
    
    device_path = args.device.encode('utf-8')
    method_id = METHODS[args.method]
    
    if os.geteuid() != 0:
        print("Warning: You are not running as root. Wiping specific partitions or block devices requires root privileges.")
    
    print(f"Starting wipe on {args.device} using {args.method}...")
    print("WARNING: All data on this device will be permanently destroyed.")
    confirm = input("Type 'CONFIRM' to proceed: ")
    
    if confirm != "CONFIRM":
        print("Operation cancelled.")
        return

    start_time = time.time()
    
    # Create callback
    cb = PROGRESS_CALLBACK(progress_handler)
    
    try:
        result = wiper.wipe_drive(device_path, method_id, cb)
        print() # Newline after progress bar
        
        if result == 0:
            print(f"Wipe completed successfully in {time.time() - start_time:.2f} seconds.")
            
            if args.verify > 0:
                print(f"Verifying {args.verify} random spots...")
                v_result = wiper.verify_drive(device_path, args.verify)
                if v_result:
                    print("Verification PASSED. Drive appears clean.")
                else:
                    print("Verification FAILED! Non-zero data found.")
                    sys.exit(1)
        else:
            print(f"Wipe error: System error code {result}")
            sys.exit(result)
            
    except KeyboardInterrupt:
        print("\n\nUser cancelled operation.")
        wiper.cancel_wipe()
        sys.exit(130)

if __name__ == "__main__":
    main()
