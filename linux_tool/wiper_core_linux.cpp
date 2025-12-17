#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/fs.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <cerrno>

// Min macro
#define MIN(a,b) (((a)<(b))?(a):(b))

// Progress callback type
typedef void (*ProgressCallback)(double progress, uint64_t total, uint64_t current, int pass, int total_passes);

// Global cancellation flag
static volatile bool g_cancel_requested = false;

// Method enumeration
#define METHOD_NIST_CLEAR 0
#define METHOD_NIST_PURGE 1
#define METHOD_DOD_3PASS 2
#define METHOD_DOD_7PASS 3
#define METHOD_GUTMANN 4

// Buffer size (4MB for optimal performance)
#define BUFFER_SIZE (4 * 1024 * 1024)

// Hardware random generation
bool fill_random(uint8_t* buffer, size_t size) {
    size_t generated = 0;
    while (generated < size) {
        ssize_t result = getrandom(buffer + generated, size - generated, 0);
        if (result < 0) {
            if (errno == EINTR) continue;
            return false;
        }
        generated += result;
    }
    return true;
}

// Single pass wipe with real-time progress
bool wipe_pass(int fd, uint64_t total_size, uint8_t pattern_type, uint8_t* pattern, 
               int pass_num, int total_passes, ProgressCallback callback) {
    
    // Allocate buffer aligned to page size for O_DIRECT
    void* buffer_ptr;
    if (posix_memalign(&buffer_ptr, 4096, BUFFER_SIZE) != 0) return false;
    uint8_t* buffer = (uint8_t*)buffer_ptr;
    
    // Pre-fill buffer based on pattern type
    if (pattern_type == 0) {
        // Fixed pattern (0x00 or 0xFF etc)
        memset(buffer, pattern[0], BUFFER_SIZE);
    }
    
    // Seek to start
    if (lseek(fd, 0, SEEK_SET) == (off_t)-1) {
        free(buffer);
        return false;
    }
    
    uint64_t written_total = 0;
    
    while (written_total < total_size && !g_cancel_requested) {
        size_t to_write = (size_t)MIN((uint64_t)BUFFER_SIZE, total_size - written_total);
        
        // Handle O_DIRECT alignment requirements at the end of the disk
        // If the remaining size is not a multiple of the block size, we might need to handle it carefully.
        // For simplicity in this core port, we assume total_size is block aligned or we accept write errors at the very end
        // if using O_DIRECT. However, if we fail with O_DIRECT, we might want to fallback, but for now we'll stick to 512b chunks usually.
        
        // Generate random if needed
        if (pattern_type == 1) { // Random
            if (!fill_random(buffer, to_write)) {
                // Fallback to pseudo-random
                for (size_t i = 0; i < to_write; i++) {
                    buffer[i] = (uint8_t)rand();
                }
            }
        }
        
        ssize_t bytes_written = write(fd, buffer, to_write);
        if (bytes_written <= 0) {
            free(buffer);
            return false;
        }
        
        written_total += bytes_written;
        
        // Progress callback
        if (callback) {
            double base_progress = (double)(pass_num - 1) / total_passes;
            double pass_progress = ((double)written_total / total_size) / total_passes;
            double total_progress = base_progress + pass_progress;
            
            callback(total_progress, total_size, written_total, pass_num, total_passes);
        }
    }
    
    // Flush buffers
    fsync(fd);
    free(buffer);
    
    return !g_cancel_requested;
}


extern "C" {

// Main wipe function
int wipe_drive(const char* device_path, int method, ProgressCallback callback) {
    
    g_cancel_requested = false;
    
    // Open drive with exclusive access, direct I/O for performance and security
    // O_DIRECT bypasses page cache. O_SYNC ensures writes are flushed.
    int fd = open(device_path, O_RDWR | O_SYNC | O_DIRECT | O_EXCL);
    if (fd < 0) {
        // Retry without O_DIRECT if it fails (e.g. tmpfs or special files)
        fd = open(device_path, O_RDWR | O_SYNC | O_EXCL);
        if (fd < 0) return errno;
    }
    
    // Get drive size
    uint64_t total_size = 0;
    if (ioctl(fd, BLKGETSIZE64, &total_size) < 0) {
        // If ioctl fails try stat (for regular files)
        struct stat st;
        if (fstat(fd, &st) == 0) {
            total_size = st.st_size;
        } else {
            close(fd);
            return errno;
        }
    }
    
    bool success = true;
    
    // Patterns
    uint8_t zero_pattern[] = {0x00};
    uint8_t ones_pattern[] = {0xFF};
    uint8_t alt1_pattern[] = {0x55};
    uint8_t alt2_pattern[] = {0xAA};
    
    switch (method) {
        case METHOD_NIST_CLEAR: // 1 Pass Zeros
            success = wipe_pass(fd, total_size, 0, zero_pattern, 1, 1, callback);
            break;
            
        case METHOD_NIST_PURGE: // 1 Pass Random
            success = wipe_pass(fd, total_size, 1, NULL, 1, 1, callback);
            break;
            
        case METHOD_DOD_3PASS: // 3 Pass
            success = wipe_pass(fd, total_size, 0, zero_pattern, 1, 3, callback);
            if (success) success = wipe_pass(fd, total_size, 0, ones_pattern, 2, 3, callback);
            if (success) success = wipe_pass(fd, total_size, 1, NULL, 3, 3, callback);
            break;
            
        case METHOD_DOD_7PASS: // 7 Pass
            success = wipe_pass(fd, total_size, 0, zero_pattern, 1, 7, callback);
            if (success) success = wipe_pass(fd, total_size, 0, ones_pattern, 2, 7, callback);
            if (success) success = wipe_pass(fd, total_size, 1, NULL, 3, 7, callback);
            if (success) success = wipe_pass(fd, total_size, 0, zero_pattern, 4, 7, callback);
            if (success) success = wipe_pass(fd, total_size, 0, zero_pattern, 5, 7, callback);
            if (success) success = wipe_pass(fd, total_size, 0, ones_pattern, 6, 7, callback);
            if (success) success = wipe_pass(fd, total_size, 1, NULL, 7, 7, callback);
            break;
            
        case METHOD_GUTMANN: // 35 Pass
            // Random 1-4
            for (int i = 1; i <= 4 && success; i++) {
                success = wipe_pass(fd, total_size, 1, NULL, i, 35, callback);
            }
            // Alternating 5-31
            for (int i = 5; i <= 31 && success; i++) {
                uint8_t* pat = (i % 2 == 0) ? alt1_pattern : alt2_pattern;
                success = wipe_pass(fd, total_size, 0, pat, i, 35, callback);
            }
            // Random 32-35
            for (int i = 32; i <= 35 && success; i++) {
                success = wipe_pass(fd, total_size, 1, NULL, i, 35, callback);
            }
            break;
            
        default:
            success = false;
    }
    
    // Send final 100% completion callback
    if (success && callback) {
        int passes = 1;
        if (method == METHOD_DOD_3PASS) passes = 3;
        else if (method == METHOD_DOD_7PASS) passes = 7;
        else if (method == METHOD_GUTMANN) passes = 35;
        callback(1.0, total_size, total_size, passes, passes);
    }
    
    close(fd);
    if (!success) {
        return errno ? errno : 1; 
    }
    return 0; // Success
}

// Verification function
int verify_drive(const char* device_path, int num_checks) {
    
    int fd = open(device_path, O_RDONLY);
    if (fd < 0) return 0; // False
    
    uint64_t total_size = 0;
    if (ioctl(fd, BLKGETSIZE64, &total_size) < 0) {
        struct stat st;
        if (fstat(fd, &st) == 0) total_size = st.st_size;
        else { close(fd); return 0; }
    }
    
    uint8_t check_byte;
    
    for (int i = 0; i < num_checks; i++) {
        // Random offset
        uint64_t offset = 0;
        getrandom(&offset, sizeof(offset), 0);
        offset = offset % total_size;
        
        if (lseek(fd, offset, SEEK_SET) == (off_t)-1) {
            close(fd);
            return 0;
        }
        
        if (read(fd, &check_byte, 1) != 1) {
            close(fd);
            return 0;
        }
        
        if (check_byte != 0x00) {
            close(fd);
            return 0; // Found non-zero byte
        }
    }
    
    close(fd);
    return 1; // Success (True)
}

// Cancel function
void cancel_wipe() {
    g_cancel_requested = true;
}

} // extern "C"
