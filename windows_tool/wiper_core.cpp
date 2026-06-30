#include <windows.h>
#include <winioctl.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#ifndef IOCTL_DISK_GET_LENGTH_INFO
#define IOCTL_DISK_GET_LENGTH_INFO CTL_CODE(IOCTL_DISK_BASE, 0x0017, METHOD_BUFFERED, FILE_READ_ACCESS)
typedef struct _GET_LENGTH_INFORMATION {
    LARGE_INTEGER Length;
} GET_LENGTH_INFORMATION, *PGET_LENGTH_INFORMATION;
#endif

#define MIN(a,b) (((a)<(b))?(a):(b))

typedef void (*ProgressCallback)(double progress, uint64_t total, uint64_t current, int pass, int total_passes);

static volatile BOOL g_cancel_requested = FALSE;

#define METHOD_NIST_CLEAR 0
#define METHOD_NIST_PURGE 1
#define METHOD_DOD_3PASS 2
#define METHOD_DOD_7PASS 3
#define METHOD_GUTMANN 4

#define BUFFER_SIZE (4 * 1024 * 1024)

BOOLEAN fill_random(BYTE* buffer, DWORD size) {
    typedef BOOLEAN (WINAPI *RtlGenRandomProc)(PVOID, ULONG);
    HMODULE advapi = LoadLibraryA("advapi32.dll");
    if (!advapi) return FALSE;
    
    RtlGenRandomProc RtlGenRandom = (RtlGenRandomProc)GetProcAddress(advapi, "SystemFunction036");
    if (!RtlGenRandom) {
        FreeLibrary(advapi);
        return FALSE;
    }
    
    BOOLEAN result = RtlGenRandom(buffer, size);
    FreeLibrary(advapi);
    return result;
}

BOOL wipe_pass(HANDLE hDrive, uint64_t total_size, BYTE pattern_type, BYTE* pattern, 
               int pass_num, int total_passes, ProgressCallback callback) {
    
    BYTE* buffer = (BYTE*)VirtualAlloc(NULL, BUFFER_SIZE, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!buffer) return FALSE;
    
    if (pattern_type == 0) {
        memset(buffer, pattern[0], BUFFER_SIZE);
    }
    
    LARGE_INTEGER pos;
    pos.QuadPart = 0;
    SetFilePointerEx(hDrive, pos, NULL, FILE_BEGIN);
    
    uint64_t written_total = 0;
    DWORD bytes_written;
    
    while (written_total < total_size && !g_cancel_requested) {
        DWORD to_write = (DWORD)MIN((uint64_t)BUFFER_SIZE, total_size - written_total);
        
        if (pattern_type == 1) { 
            if (!fill_random(buffer, to_write)) {
                for (DWORD i = 0; i < to_write; i++) {
                    buffer[i] = (BYTE)rand();
                }
            }
        }
        
        if (!WriteFile(hDrive, buffer, to_write, &bytes_written, NULL)) {
            VirtualFree(buffer, 0, MEM_RELEASE);
            return FALSE;
        }
        
        written_total += bytes_written;
        
        if (callback) {
            double base_progress = (double)(pass_num - 1) / total_passes;
            double pass_progress = ((double)written_total / total_size) / total_passes;
            double total_progress = base_progress + pass_progress;
            
            callback(total_progress, total_size, written_total, pass_num, total_passes);
        }
    }
    
    FlushFileBuffers(hDrive);
    VirtualFree(buffer, 0, MEM_RELEASE);
    
    return !g_cancel_requested;
}

extern "C" __declspec(dllexport)
int wipe_drive(const char* device_path, int method, ProgressCallback callback) {
    
    g_cancel_requested = FALSE;
    
    HANDLE hToken;
    if (OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken)) {
        TOKEN_PRIVILEGES tp;
        LUID luid;
        
        if (LookupPrivilegeValue(NULL, SE_MANAGE_VOLUME_NAME, &luid)) {
            tp.PrivilegeCount = 1;
            tp.Privileges[0].Luid = luid;
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
            AdjustTokenPrivileges(hToken, FALSE, &tp, 0, NULL, NULL);
        }
        
        CloseHandle(hToken);
    }
    
    HANDLE hDrive = CreateFileA(
        device_path,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE, 
        NULL,
        OPEN_EXISTING,
        0, 
        NULL
    );
    
    if (hDrive == INVALID_HANDLE_VALUE) {
        DWORD error = GetLastError();
        return error;
    }
    
    DWORD bytesReturned;
    
    DeviceIoControl(hDrive, FSCTL_LOCK_VOLUME, NULL, 0, NULL, 0, &bytesReturned, NULL);
    
    DeviceIoControl(hDrive, FSCTL_DISMOUNT_VOLUME, NULL, 0, NULL, 0, &bytesReturned, NULL);
    
    LARGE_INTEGER size;
    if (!GetFileSizeEx(hDrive, &size)) {
        DWORD returned;
        GET_LENGTH_INFORMATION lengthInfo;
        if (!DeviceIoControl(hDrive, IOCTL_DISK_GET_LENGTH_INFO, NULL, 0, 
                            &lengthInfo, sizeof(lengthInfo), &returned, NULL)) {
            CloseHandle(hDrive);
            return GetLastError();
        }
        size.QuadPart = lengthInfo.Length.QuadPart;
    }
    
    uint64_t total_size = size.QuadPart;
    BOOL success = TRUE;
    
    BYTE zero_pattern[] = {0x00};
    BYTE ones_pattern[] = {0xFF};
    BYTE alt1_pattern[] = {0x55};
    BYTE alt2_pattern[] = {0xAA};
    
    switch (method) {
        case METHOD_NIST_CLEAR: 
            success = wipe_pass(hDrive, total_size, 0, zero_pattern, 1, 1, callback);
            break;
            
        case METHOD_NIST_PURGE: 
            success = wipe_pass(hDrive, total_size, 1, NULL, 1, 1, callback);
            break;
            
        case METHOD_DOD_3PASS: 
            success = wipe_pass(hDrive, total_size, 0, zero_pattern, 1, 3, callback);
            if (success) success = wipe_pass(hDrive, total_size, 0, ones_pattern, 2, 3, callback);
            if (success) success = wipe_pass(hDrive, total_size, 1, NULL, 3, 3, callback);
            break;
            
        case METHOD_DOD_7PASS: 
            success = wipe_pass(hDrive, total_size, 0, zero_pattern, 1, 7, callback);
            if (success) success = wipe_pass(hDrive, total_size, 0, ones_pattern, 2, 7, callback);
            if (success) success = wipe_pass(hDrive, total_size, 1, NULL, 3, 7, callback);
            if (success) success = wipe_pass(hDrive, total_size, 0, zero_pattern, 4, 7, callback);
            if (success) success = wipe_pass(hDrive, total_size, 0, zero_pattern, 5, 7, callback);
            if (success) success = wipe_pass(hDrive, total_size, 0, ones_pattern, 6, 7, callback);
            if (success) success = wipe_pass(hDrive, total_size, 1, NULL, 7, 7, callback);
            break;
            
        case METHOD_GUTMANN: 
            for (int i = 1; i <= 4 && success; i++) {
                success = wipe_pass(hDrive, total_size, 1, NULL, i, 35, callback);
            }
            for (int i = 5; i <= 31 && success; i++) {
                BYTE* pat = (i % 2 == 0) ? alt1_pattern : alt2_pattern;
                success = wipe_pass(hDrive, total_size, 0, pat, i, 35, callback);
            }
            for (int i = 32; i <= 35 && success; i++) {
                success = wipe_pass(hDrive, total_size, 1, NULL, i, 35, callback);
            }
            break;
            
        default:
            success = FALSE;
    }
    
    if (success && callback) {
        int passes = 1;
        if (method == METHOD_DOD_3PASS) passes = 3;
        else if (method == METHOD_DOD_7PASS) passes = 7;
        else if (method == METHOD_GUTMANN) passes = 35;
        callback(1.0, total_size, total_size, passes, passes);
    }
    
    CloseHandle(hDrive);
    if (!success) {
        DWORD error = GetLastError();
        return error ? error : 1; 
    }
    return 0; 
}

extern "C" __declspec(dllexport)
BOOL verify_drive(const char* device_path, int method, int num_checks) {
    
    HANDLE hDrive = CreateFileA(device_path, GENERIC_READ, FILE_SHARE_READ, 
                                NULL, OPEN_EXISTING, 0, NULL);
    if (hDrive == INVALID_HANDLE_VALUE) return FALSE;
    
    LARGE_INTEGER size;
    DWORD returned;
    GET_LENGTH_INFORMATION lengthInfo;
    if (!DeviceIoControl(hDrive, IOCTL_DISK_GET_LENGTH_INFO, NULL, 0, 
                        &lengthInfo, sizeof(lengthInfo), &returned, NULL)) {
        CloseHandle(hDrive);
        return FALSE;
    }
    
    uint64_t total_size = lengthInfo.Length.QuadPart;
    if (total_size < 512) {
        CloseHandle(hDrive);
        return FALSE;
    }
    
    BYTE buffer[512];
    DWORD bytes_read;
    
    for (int i = 0; i < num_checks; i++) {
        uint64_t offset = ((uint64_t)rand() << 32 | rand()) % (total_size - 512);
        
        LARGE_INTEGER pos;
        pos.QuadPart = offset;
        SetFilePointerEx(hDrive, pos, NULL, FILE_BEGIN);
        
        if (!ReadFile(hDrive, buffer, 512, &bytes_read, NULL) || bytes_read != 512) {
            CloseHandle(hDrive);
            return FALSE;
        }
        
        if (method == METHOD_NIST_CLEAR) {
            // NIST Clear: must be all zeros
            for (DWORD j = 0; j < bytes_read; j++) {
                if (buffer[j] != 0x00) {
                    CloseHandle(hDrive);
                    return FALSE;
                }
            }
        } else {
            // Other methods write random data or non-zero patterns.
            // Check that the block is NOT all zeros and NOT all ones (0xFF).
            BOOL all_zeros = TRUE;
            BOOL all_ones = TRUE;
            for (DWORD j = 0; j < bytes_read; j++) {
                if (buffer[j] != 0x00) all_zeros = FALSE;
                if (buffer[j] != 0xFF) all_ones = FALSE;
            }
            if (all_zeros || all_ones) {
                CloseHandle(hDrive);
                return FALSE;
            }
        }
    }
    
    CloseHandle(hDrive);
    return TRUE;
}

extern "C" __declspec(dllexport)
void cancel_wipe() {
    g_cancel_requested = TRUE;
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    return TRUE;
}
