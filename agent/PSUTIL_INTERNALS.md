# psutil Internals - How System Monitoring Works at the OS Level

## Overview

This document explains how `psutil` works under the hood, specifically focusing on Linux internals. Understanding these concepts helps you appreciate how the SysSight Agent collects system metrics and why certain approaches are used.

---

## Linux Architecture: The `/proc` Filesystem

### What is `/proc`?

`/proc` is a **virtual filesystem** that provides an interface to kernel data structures. It doesn't exist on disk - it's generated on-the-fly by the kernel.

**Key Points**:
- Every read from `/proc` triggers a kernel function
- Kernel returns current system state
- No caching - always up-to-date
- **Read-only** (mostly)

```bash
$ ls /proc/
1/        10/     200/   300/   ...    uptime    version    loadavg
# Numbers are process PIDs
# Files like 'uptime', 'version', 'loadavg' contain system info
```

### Why `/proc` Exists

Before `/proc`:
- System calls required C programming
- Kernel internal structures not accessible from userspace
- Performance monitoring difficult

With `/proc`:
- Human-readable format
- Standard filesystem APIs
- No special privileges needed
- Unix philosophy: everything is a file

---

## How psutil Uses `/proc` - Function by Function

### 1. CPU Usage: `cpu_percent()`

#### Traditional Approach (without psutil)

```bash
$ cat /proc/stat
cpu  12345 0 4567 891011 0 0 0 0 0 0
```

**What does this mean?**
```c
struct cpu_stat {
    unsigned long user_time      // 12345 - time in user mode
    unsigned long nice_time      // 0 - time in nice'd user mode  
    unsigned long system_time    // 4567 - time in system/kernel mode
    unsigned long idle_time       // 891011 - time idle
    unsigned long iowait         // 0 - waiting for I/O
    unsigned long irq           // 0 - hardware interrupts
    unsigned long softirq       // 0 - software interrupts
    unsigned long steal         // 0 - stolen time (virtualization)
}
```

**How CPU percentage is calculated**:
```python
# Read /proc/stat twice with 1-second interval
t0 = read_proc_stat()  # { user: 10000, system: 5000, idle: 90000, total: 105000 }
time.sleep(1)
t1 = read_proc_stat()  # { user: 12000, system: 6000, idle: 92000, total: 110000 }

# Calculate difference
delta_total = t1.total - t0.total  # 5000
delta_used = (t1.user + t1.system) - (t0.user + t0.system)  # 3000

# Percentage
cpu_percent = (delta_used / delta_total) * 100  # (3000 / 5000) * 100 = 60%
```

**Why wait 1 second?**
- First reading gives baseline
- Second reading shows change over time
- CPU usage = work done / time elapsed

#### What psutil Does

```python
psutil.cpu_percent(interval=1)
```

**Internal implementation** (simplified):
```python
# psutil source code (simplified)
def cpu_percent(interval=1):
    # Read /proc/stat
    stat1 = read_file('/proc/stat')
    user1, system1, idle1 = parse_cpu_line(stat1)
    total1 = user1 + system1 + idle1
    
    # Wait
    sleep(interval)  # default 1 second
    
    # Read again
    stat2 = read_file('/proc/stat')
    user2, system2, idle2 = parse_cpu_line(stat2)
    total2 = user2 + system2 + idle2
    
    # Calculate percentage
    total_delta = total2 - total1
    used_delta = ((user2 + system2) - (user1 + system1))
    
    return (used_delta / total_delta) * 100
```

**Why `interval=1`?**
- Too short (0.1s): High CPU variance, noisy readings
- Too long (10s): Stale data, poor responsiveness
- **1 second**: Good balance for monitoring dashboards

---

### 2. Memory Usage: `virtual_memory()`

#### `/proc/meminfo`

```bash
$ cat /proc/meminfo
MemTotal:        8157184 kB    # Total RAM
MemFree:         2345678 kB    # Completely free
MemAvailable:    4567890 kB    # Available to applications (includes cache)
Buffers:           12345 kB    # Block device buffers
Cached:          1234567 kB    # Page cache
SwapTotal:       8388608 kB    # Total swap
SwapFree:         876543 kB    # Free swap
```

#### What psutil Returns

```python
mem = psutil.virtual_memory()
# Returns:
{
    "total": 8157184 * 1024,      # Bytes (8GB)
    "available": 4567890 * 1024,   # Bytes available
    "percent": 56.2,               # Usage percentage
    "used": total - available,
    "free": mem_free  # Actually free (not used)
}
```

#### Key Understanding: "Available" vs "Free"

**Free Memory**: Memory that's truly unused
```c
free = mem_free  // 2345678 KB
```

**Available Memory**: Memory that can be freed if needed
```c
available = free + cache + buffers - reserved_for_kernel
// = 2345678 + 1234567 + 12345 - overhead
// = 4567890 KB
```

**Why this matters**:
- Linux uses RAM for disk cache (makes disk I/O fast)
- Cache can be freed instantly for applications
- "Available" tells you what memory is actually usable

**psutil Insight**:
```python
# psutil calculates available as: free + page_cache - min_kernel_reserved
available = free + (cached + buffers) - (some_kernel_reserved)
```

---

### 3. Disk Usage: `disk_usage('/')`

#### `/proc/mounts` and `statvfs()`

**Mount points**:
```bash
$ cat /proc/mounts
/dev/sda1 / ext4 rw,relatime 0 0
/dev/sda2 /home ext4 rw,relatime 0 0
```

**Filesystem statistics**:
```c
#include <sys/statvfs.h>

struct statvfs {
    unsigned long f_blocks;    // Total blocks in filesystem
    unsigned long f_bfree;     // Free blocks
    unsigned long f_bavail;    // Available blocks (for non-root)
    unsigned long f_files;     // Total inodes
    unsigned long f_ffree;     // Free inodes
};
```

#### How psutil Gets Disk Info

```python
import psutil
disk = psutil.disk_usage('/')
```

**System call chain**:
```c
// Python psutil.c (simplified)
disk_usage(path) {
    // Call Linux statvfs() system call
    statvfs(path, &statbuf);
    
    // Calculate sizes
    total = statbuf.f_blocks * block_size;
    free = statbuf.f_bfree * block_size;
    used = total - free;
    
    return { total, used, free, percent };
}
```

**Linux system call**: `statvfs()` - gets filesystem statistics

**No `/proc` involved**: Uses direct system call for efficiency

---

### 4. Network I/O: `net_io_counters()`

#### `/proc/net/dev`

```bash
$ cat /proc/net/dev
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 123456789  123456    0    0    0     0          0         0  123456789  123456    0    0    0     0       0          0
 eth0: 876543210  876543    0    0    0     0          0         0  987654321  987654    0    0    0     0       0          0
 wlan0: 234567890  234567    0    0    0     0          0         0  123456789  123456    0    0    0     0       0          0
```

**What psutil reads**:
```python
net = psutil.net_io_counters()
# Returns:
{
    "bytes_sent": sum(all interfaces.bytes_sent),
    "bytes_recv": sum(all interfaces.bytes_recv),
    "packets_sent": sum(all interfaces.packets_sent),
    "packets_recv": sum(all interfaces.packets_recv)
}
```

**Cumulative since boot**:
- Values increase monotonically
- Need to calculate deltas for current rate
- Reboot resets counters to zero

---

### 5. Load Average: `getloadavg()`

#### `/proc/loadavg`

```bash
$ cat /proc/loadavg
1.23 2.45 3.67 12/234 56789

Meaning:
  1.23  - 1-minute load average
  2.45  - 5-minute load average  
  3.67  - 15-minute load average
  12/234 - Currently running processes / Total processes
  56789  - Last PID assigned
```

**What is "load average"?**

Load average represents the **average number of processes that are either running or waiting for CPU time**.

```
Load average = 1.0 on 4-core CPU:
- 1 CPU worth of work being done
- 4 cores available → 25% utilization

Load average = 8.0 on 4-core CPU:
- 8 CPUs worth of work
- 4 cores available → 200% utilization (overloaded!)
```

**Why three values (1m, 5m, 15m)?**
- **1-minute**: Short-term spikes (serves a request)
- **5-minute**: Medium-term trends (handling burst)
- **15-minute**: Long-term trend (sustained load)

**Example**:
```bash
# CPU-intensive task starts at t=0
t=0m:  load=1.0 (idle)
t=1m:  load=4.5 (sudden spike)
t=5m:  load=4.0 (still high)
t=10m: load=2.0 (decreasing)
t=15m: load=1.0 (back to idle)
```

**psutil implementation**:
```python
import os
load_1m, load_5m, load_15m = os.getloadavg()

# No /proc involved - direct syscall
# Calls Linux getloadavg() system call
```

---

### 6. Process Information: `process_iter()`

#### `/proc/{pid}/stat`

**For a single process**:
```bash
$ cat /proc/1234/stat
1234 (python) S 1 1234 1234 0 -1 1077952832 ...

Fields (position-based):
[1] pid = 1234
[2] comm = python
[3] state = S (sleeping)
[6] starttime = 1077952832
...
```

**psutil reads**:
```python
with open(f'/proc/{pid}/stat', 'r') as f:
    fields = f.read().split()
    pid = int(fields[0])
    name = fields[1].strip('()')
    state = fields[2]
    # ... parse other fields
```

#### `/proc/{pid}/status`

More human-readable process info:
```bash
$ cat /proc/1234/status
Name:   python
State:  S (sleeping)
Pid:    1234
PPid:   1
VmRSS:  123456 kB        # Physical memory used
VmSize: 2345678 kB       # Virtual memory size
Threads: 4
```

#### `/proc/{pid}/io` (for I/O stats)

```bash
$ cat /proc/1234/io
rchar: 123456789        # Bytes read
wchar: 987654321        # Bytes written
read_bytes: 567890      # Bytes read from disk
write_bytes: 123456     # Bytes written to disk
```

---

## How psutil Implements These Functions

### Architecture Overview

```
Python Application (agent.py)
    ↓ (import psutil)
Python psutil Module
    ↓ (calls C functions)
C Extension (psutil/_psutil_linux.c)
    ↓ (Linux system calls)
Linux Kernel
    ↓ (reads from)
/proc filesystem (virtual)
```

### Hybrid Implementation

**Python layer** (user-friendly API):
```python
# psutil/__init__.py
def cpu_percent(interval=1):
    """Returns CPU usage as percentage"""
    return psutil_platform.cpu_percent(interval)
```

**C layer** (efficient system access):
```c
// psutil/_psutil_linux.c
static PyObject *cpu_percent(PyObject *self, PyObject *args) {
    int interval = 1;
    if (!PyArg_ParseTuple(args, "i", &interval))
        return NULL;
    
    // Open /proc/stat
    FILE *f = fopen("/proc/stat", "r");
    // Read and parse
    // ... return CPU percent
}
```

**Why C?**:
- Faster file I/O
- Direct system call access
- Lower overhead

### Process Enumeration

**How `process_iter()` works**:

```python
# psutil implementation (simplified)
def process_iter(attrs=None):
    # List all /proc directories
    pids = []
    for filename in os.listdir('/proc'):
        if filename.isdigit():
            pids.append(int(filename))
    
    # For each PID, read process info
    for pid in pids:
        try:
            proc = Process(pid, attr_names=attrs)
            yield proc
        except (NoSuchProcess, AccessDenied):
            # Skip processes that vanished or are inaccessible
            continue
```

**Optimization**: Uses `attr_names` parameter
```python
# Only fetch specified attributes
for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
    info = proc.info
    # info contains only requested fields
```

**Why**: Reading `/proc/{pid}/stat` is fast, but reading for 1000+ processes adds up.

---

## Performance Characteristics

### File I/O Patterns

#### Reading CPU Stats
```python
# psutil reads from /proc/stat
start = time.time()
psutil.cpu_percent(interval=0.1)
elapsed = time.time() - start
# elapsed ≈ 100ms (mostly the sleep)
```

**Cost**: 
- Open file: ~0.01ms
- Read file: ~0.01ms
- Parse: ~0.01ms
- Sleep: 100ms (interval)

**Total**: ~100.03ms

#### Reading Memory Stats
```python
# psutil reads from /proc/meminfo
start = time.time()
mem = psutil.virtual_memory()
elapsed = time.time() - start
# elapsed ≈ 0.01ms
```

**Why so fast?**:
- Single file read
- Small file (~100 bytes)
- In-memory (virtual filesystem)

#### Process Enumeration
```python
# psutil reads from /proc for each process
start = time.time()
processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent']))
elapsed = time.time() - start
# elapsed ≈ 50-200ms (depends on process count)
```

**Scales with**:
- Number of processes (can be hundreds)
- Permission checks (some processes may be inaccessible)
- Attribute fetching (more attrs = slower)

**Optimization**:
```python
# Good: Only fetch what you need
for proc in psutil.process_iter(['pid', 'name']):
    ...

# Bad: Fetching all attributes
for proc in psutil.process_iter():
    info = proc.info  # Includes 50+ fields
```

---

## Why These Design Decisions Matter for SysSight Agent

### 1. CPU Percent with 1-Second Interval

**Why not 0.1 seconds?**
```python
# Current approach
cpu_percent(interval=1)  # 1-second sample

# More frequent
cpu_percent(interval=0.1)  # 0.1-second sample
```

**Trade-offs**:
- **Faster polling**: More data points, but higher CPU overhead
- **Current**: Balance between freshness and overhead

**For monitoring**: 1-second is sufficient (no need for sub-second granularity)

### 2. Cumulative Network Counters

**Backend stores raw bytes, not rate**:
```python
# Agent sends
{
    "bytes_sent": 1234567890,    # Cumulative since boot
    "bytes_received": 9876543210
}

# Why not calculate rate in agent?
# - Agent doesn't need to track previous values
# - Backend can calculate rate from timestamps
# - Simpler agent code
```

**Frontend calculates rate**:
```typescript
// When displaying
const rate = (current.bytes_sent - previous.bytes_sent) / (current.timestamp - previous.timestamp)
```

### 3. Process Enumeration Optimization

**Agent uses attribute filtering**:
```python
# Efficient
for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
    info = proc.info
    # Only reads requested fields
```

**Why**: Reading `/proc/{pid}/stat` 1000+ times is slow. Only fetch what's needed.

### 4. Error Handling Strategy

**Graceful degradation**:
```python
try:
    processes = get_process_list()
    # Some processes may be inaccessible
except (psutil.NoSuchProcess, psutil.AccessDenied):
    # Skip and continue with others
    continue
```

**Why**:
- System processes may have restricted access
- Processes can disappear during iteration
- Better to return partial data than fail completely

---

## Linux-Specific Behaviors

### 1. Zombie Processes

**What is a zombie?**
```
[PID 1234] (zombie)
    - Parent process hasn't read exit status yet
    - Process has exited, but PID still exists
    - Taking up memory space (minimal)
```

**Why psutil skips them**:
```python
try:
    proc = psutil.Process(pid)
    # Access denied for zombies
except psutil.ZombieProcess:
    continue  # Skip zombie processes
```

**Result**: Agent doesn't report zombie PIDs

### 2. Kernel Threads

**What are kernel threads?**
```
[kthreadd] - Kernel thread daemon
[rcu_gp]   - RCU grace period thread
[migration] - CPU migration thread
```

**Why ignore them?**
- Not user processes
- Misleading in process lists
- psutil includes them (can be filtered)

### 3. Cached vs Used Memory

**Linux memory management**:
```c
Total RAM: 8GB
├─ Used by applications: 2GB
├─ Cached (available): 4GB  ← Can be freed
└─ Kernel reserved: 2GB
```

**psutil returns "available"**:
```python
mem = psutil.virtual_memory()
# mem.available = 4GB (2GB free + 2GB cache)
```

**Why**: More accurate representation of usable memory

### 4. Multi-Core CPU Usage

**`cpu_percent()` returns system-wide average**:
```python
psutil.cpu_percent(interval=1)  # Returns: 45.0%

# If 4-core CPU:
# - Core 1: 100% (busy)
# - Core 2: 0% (idle)
# - Core 3: 50% (half busy)
# - Core 4: 30% (idle)

# Average: (100 + 0 + 50 + 30) / 4 = 45%
```

**Per-core usage**:
```python
psutil.cpu_percent(interval=1, percpu=True)
# Returns: [100.0, 0.0, 50.0, 30.0]
```

---

## System Call Reference

### Key Linux System Calls Used by psutil

#### `open()`
```c
int fd = open("/proc/stat", O_RDONLY);
```
Opens `/proc/stat` file

#### `read()`
```c
char buffer[4096];
ssize_t n = read(fd, buffer, sizeof(buffer));
```
Reads file contents

#### `statvfs()`
```c
struct statvfs st;
statvfs("/", &st);
```
Gets filesystem statistics

#### `getloadavg()`
```c
double loadavg[3];
getloadavg(loadavg, 3);
```
Gets load averages

#### `readdir()`
```c
DIR *dir = opendir("/proc");
struct dirent *entry;
while ((entry = readdir(dir)) != NULL) {
    // Check if entry is numeric (PID)
}
```
Lists directories

---

## Security and Permissions

### Reading Process Information

**All users can read**:
- `/proc/stat` (system-wide CPU stats)
- `/proc/meminfo` (memory info)
- `/proc/loadavg` (load averages)

**Own processes only**:
- `/proc/{pid}/stat` - Can read own processes
- `/proc/{pid}/status` - Can read own processes

**Privileged read (some require root)**:
- `/proc/{pid}/io` - I/O stats for other processes
- `/proc/{pid}/net` - Network connections for other processes
- `/proc/kmsg` - Kernel messages (requires root)

**SysSight Agent**:
- Runs as regular user (not root)
- Can read most system information
- Cannot read other users' processes (intentional security)

---

## Practical Examples from SysSight Agent

### How Agent Collects CPU

```python
def get_cpu_percent():
    return psutil.cpu_percent(interval=1)
```

**What happens**:
1. psutil opens `/proc/stat`
2. Reads current counters
3. Sleeps for 1 second
4. Reads again
5. Calculates percentage
6. Returns to agent

**Total time**: ~1.02 seconds

### How Agent Collects Memory

```python
def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "percent_used": mem.percent
    }
```

**What happens**:
1. psutil opens `/proc/meminfo`
2. Parses ~20 lines
3. Calculates available = free + cache - reserved
4. Returns immediately

**Total time**: ~0.01ms

### How Agent Collects Processes

```python
def get_process_list():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "cpu_percent": round(info['cpu_percent'] or 0, 2),
                "memory_percent": round(info['memory_percent'] or 0, 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes
```

**What happens**:
1. psutil lists `/proc/*` directories (PIDs)
2. For each PID, reads `/proc/{pid}/stat`
3. Parses stat file
4. Handles errors gracefully
5. Returns list

**Total time**: ~50-200ms (depends on process count)

---

## Conclusion

Understanding these internals helps you:
1. **Optimize agent code**: Know which operations are fast/slow
2. **Debug issues**: Understand why certain metrics behave differently
3. **Design systems**: Make informed decisions about polling intervals
4. **Explain in interviews**: Show deep understanding of Linux internals

**Key Takeaways**:
- `/proc` is a virtual filesystem providing kernel data
- psutil efficiently reads `/proc` files
- CPU percentage requires time-based sampling
- Memory "available" includes cache (more accurate than "free")
- Process enumeration scales with number of processes
- Error handling is crucial for production systems

This knowledge makes you a better systems engineer, not just a Python programmer.


