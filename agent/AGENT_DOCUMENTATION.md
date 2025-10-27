# SysSight Agent - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Files and Structure](#files-and-structure)
4. [Dependencies](#dependencies)
5. [Core Components](#core-components)
6. [Threading Architecture](#threading-architecture)
7. [Function Reference](#function-reference)
8. [Data Flow](#data-flow)
9. [Configuration](#configuration)
10. [Error Handling](#error-handling)

---

## Overview

The SysSight Agent is a lightweight system monitoring agent that runs on remote hosts to collect system metrics and send them to a central server. It's designed to be lightweight, resilient, and autonomous, operating as a background service that continuously monitors system health.

### Key Responsibilities
- **Metric Collection**: Gathers CPU, memory, disk, network, and process data
- **Threshold Monitoring**: Evaluates metrics against configurable thresholds
- **Alert Generation**: Sends alerts when thresholds are violated
- **Process Serving**: Provides a local API endpoint for real-time process information
- **Server Communication**: Maintains bidirectional communication with the central server

---

## Architecture

The agent follows a multi-threaded architecture with the following design patterns:

1. **Singleton Agent Pattern**: One instance manages all operations
2. **Threading for Concurrency**: Separate threads for metric collection and Flask server
3. **Session-Based Communication**: Persistent HTTP sessions for efficiency
4. **Periodic Task Execution**: Scheduled operations for registration and threshold updates
5. **Graceful Degradation**: Continues operating even if server communication fails

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     SysSight Agent                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐    ┌───────────────────────────┐    │
│  │  Main Thread     │    │   Flask Server Thread     │    │
│  │  (Agent.run)     │    │   (0.0.0.0:9090)          │    │
│  │                  │    │                           │    │
│  │  • Collect       │    │  • Process List API      │    │
│  │    Metrics       │    │  • GET /processes         │    │
│  │  • Send to       │◄───┤  • Returns JSON           │    │
│  │    Server        │    └───────────────────────────┘    │
│  │  • Check         │              │                      │
│  │    Thresholds    │              │                      │
│  │  • Register      │              │                      │
│  │  • Fetch         │              │                      │
│  │    Thresholds    │              │                      │
│  └──────────────────┘              │                      │
│           │                        │                      │
│           ▼                        ▼                      │
│  ┌──────────────────────────────────────────────────┐    │
│  │         HTTP Session (requests.Session)          │    │
│  │  • Persistent TCP connections                   │    │
│  │  • Bearer token authentication                  │    │
│  │  • Timeout handling                             │    │
│  └──────────────────────────────────────────────────┘    │
│           │                                              │
└───────────┼──────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│                    Central Server                         │
│  • POST /metrics (receive metrics)                       │
│  • POST /api/v1/agents/register (agent registration)    │
│  • GET /api/v1/thresholds (fetch threshold configs)     │
│  • POST /api/v1/alerts (receive alerts)                 │
└──────────────────────────────────────────────────────────┘
```

---

## Files and Structure

### `agent.py`
The main agent implementation file containing all monitoring logic, server communication, and alert management.

**Size**: 418 lines  
**Purpose**: Core agent functionality

### `requirements.txt`
Python package dependencies for the agent.

**Dependencies**:
- `psutil==7.1.0`: Cross-platform system and process utilities
- `requests==2.32.5`: HTTP library for server communication
- Certificate management: `certifi`, `charset-normalizer`, `idna`, `urllib3`

### `venv/`
Python virtual environment containing all installed packages and Python executables.

---

## Dependencies

### psutil (Cross-platform process and system utilities)

**Why**: Essential for collecting system metrics on Windows, Linux, and macOS.

**Key Functions Used**:
- `cpu_percent(interval=1)`: Returns CPU usage as a percentage
- `virtual_memory()`: Returns memory statistics (total, available, used, percent)
- `disk_usage(path)`: Returns disk space information
- `net_io_counters()`: Returns network I/O counters (bytes sent/received)
- `getloadavg()`: Returns system load averages (1m, 5m, 15m)
- `cpu_count()`: Returns number of CPU cores
- `process_iter()`: Iterates over all running processes
- `gethostname()`: Returns the hostname

**Error Handling**: The agent gracefully handles `NoSuchProcess`, `AccessDenied`, and `ZombieProcess` exceptions when iterating over processes.

### requests (HTTP library)

**Why**: Provides a clean, efficient API for HTTP communication with persistent sessions.

**Key Features Used**:
- `requests.Session()`: Persistent connections to reduce overhead
- Automatic connection pooling
- Header management (Authorization, Content-Type)
- Timeout handling (5 seconds for all requests)
- Exception handling (`HTTPError`, `RequestException`)

### Flask (Micro web framework)

**Why**: Lightweight HTTP server for serving process data to the central server.

**Key Features Used**:
- Route definition (`@app.route`)
- JSON response serialization (`jsonify`)
- Running in a daemon thread
- Host binding (0.0.0.0 for external access)

---

## Core Components

### 1. Metric Collection Functions (Lines 14-75)

Individual functions that collect specific system metrics. Each function is designed to be:
- **Idempotent**: No side effects, returns fresh data each call
- **Fault-tolerant**: Gracefully handles exceptions
- **Focused**: Single responsibility per function

#### `get_cpu_percent()` (Line 14-15)
```python
def get_cpu_percent():
    return psutil.cpu_percent(interval=1)
```

**Purpose**: Collects CPU utilization percentage

**How**: Uses `psutil.cpu_percent()` with a 1-second interval to get a representative sample of CPU usage across all cores.

**Why interval=1**: A 1-second sample provides accurate CPU utilization without blocking too long. The measurement includes all CPU time (user, system, idle) and returns a percentage of total CPU capacity.

**Return Value**: Float representing CPU usage percentage (0-100)

#### `get_memory_info()` (Line 17-23)
```python
def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "percent_used": mem.percent
    }
```

**Purpose**: Collects physical memory statistics

**How**: Uses `psutil.virtual_memory()` to get comprehensive memory information.

**Data Conversion**: Converts bytes to gigabytes using `1024**3` (binary gigabytes, standard in OS reporting).

**Why Rounding**: Rounding to 2 decimal places provides sufficient precision without excessive detail.

**Returns**:
- `total_gb`: Total physical memory in gigabytes
- `available_gb`: Available memory (memory available to processes)
- `percent_used`: Percentage of memory currently in use

#### `get_disk_info(path='/')` (Line 25-32)
```python
def get_disk_info(path='/'):
    disk = psutil.disk_usage(path)
    return {
        "total_gb": round(disk.total / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "percent_used": round((disk.used / disk.total) * 100, 2)
    }
```

**Purpose**: Collects disk space information for the root partition

**How**: Uses `psutil.disk_usage()` on the root filesystem.

**Note**: On Windows, this defaults to `C:\`. On Unix-like systems, it's `/`.

**Why Root Partition**: Monitors the primary storage partition to track disk exhaustion.

**Returns**:
- `total_gb`: Total disk space
- `used_gb`: Used disk space
- `free_gb`: Free disk space
- `percent_used`: Percentage of disk usage

#### `get_network_io()` (Line 34-39)
```python
def get_network_io():
    net = psutil.net_io_counters()
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_received": net.bytes_recv
    }
```

**Purpose**: Collects network I/O statistics

**How**: Uses `psutil.net_io_counters()` to get cumulative network statistics.

**Cumulative Nature**: These counters are cumulative since system boot, showing total bytes sent and received across all network interfaces.

**Why Raw Bytes**: Provides granular data that can be used to calculate network rate in the UI.

**Returns**:
- `bytes_sent`: Total bytes sent since boot
- `bytes_received`: Total bytes received since boot

#### `get_load_average()` (Line 41-51)
```python
def get_load_average():
    load_1m, load_5m, load_15m = psutil.getloadavg()
    cpu_count = psutil.cpu_count()
    return {
        "1m": load_1m,
        "5m": load_5m,
        "15m": load_15m,
        "1m_normalized": round(load_1m / cpu_count, 2),
        "5m_normalized": round(load_5m / cpu_count, 2),
        "15m_normalized": round(load_15m / cpu_count, 2)
    }
```

**Purpose**: Collects system load averages

**How**: Uses `psutil.getloadavg()` to get 1-minute, 5-minute, and 15-minute load averages.

**Load Average**: Represents the average system load (number of processes waiting for CPU time).

**Normalization**: Divides load by CPU count to get a percentage where 1.0 = 100% utilization.

**Platform Note**: On Windows, `getloadavg()` may not be available; the agent handles this gracefully.

**Returns**:
- Raw load averages (1m, 5m, 15m)
- Normalized load averages (per CPU core)

#### `get_process_list()` (Line 53-75)
```python
def get_process_list():
    """
    Collect running processes with pid, name, cpu_percent, and memory_percent.
    Handles permission errors gracefully.
    """
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                process_info = proc.info
                processes.append({
                    "pid": process_info['pid'],
                    "name": process_info['name'],
                    "cpu_percent": round(process_info['cpu_percent'] or 0, 2),
                    "memory_percent": round(process_info['memory_percent'] or 0, 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        print(f"Error collecting process list: {e}", file=sys.stderr)
    
    return processes
```

**Purpose**: Collects a snapshot of all running processes

**How**: Iterates through all processes using `psutil.process_iter()` with attribute filtering.

**Error Handling**: Catches three types of process-related exceptions:
- `NoSuchProcess`: Process terminated during iteration
- `AccessDenied`: Insufficient permissions to access process
- `ZombieProcess`: Terminated but not yet cleaned up

**Why Graceful Handling**: Some processes may terminate or become inaccessible during collection. The agent continues collecting data from accessible processes.

**Performance**: Attribute filtering reduces overhead by only fetching required fields.

**Returns**: List of process dictionaries with PID, name, CPU usage, and memory usage.

---

### 2. ThresholdEvaluator Class (Lines 77-130)

Responsible for evaluating metrics against thresholds and preventing alert spam.

#### Purpose
- Determine if collected metrics violate configured thresholds
- Prevent duplicate alerts using deduplication logic
- Support multiple severity levels (warning, critical)
- Support multiple comparison operators (>, <, >=, <=, ==)

#### Design Pattern: Deduplication with Time Window

The class uses a dictionary (`self.sent_alerts`) to track recently sent alerts, preventing spam by enforcing a minimum time between identical alerts.

```python
self.sent_alerts = {}  # Track sent alerts to prevent spam
```

**Alert Key Format**: `f"{hostname}_{metric_name}_{severity}"`

**Time Window**: 10 seconds - if an identical alert was sent within the last 10 seconds, it's skipped.

**Why 10 Seconds**: Balances alert responsiveness with spam prevention. Critical thresholds would still fire multiple times if the issue persists, but not excessively.

#### `__init__(self, thresholds)` (Line 78-80)
Initializes the evaluator with a list of threshold configurations.

**Threshold Format**:
```python
{
    'metric_name': 'cpu_percent',
    'operator': '>',
    'threshold_value': 80.0,
    'severity': 'warning'
}
```

#### `evaluate(self, metrics)` (Line 82-108)
Main evaluation method that checks all thresholds against collected metrics.

**Algorithm**:
1. Iterate through all configured thresholds
2. Check if metric violates threshold using `_check_threshold()`
3. Generate deduplication key
4. Check if alert was sent recently (within 10 seconds)
5. If new violation, add to violations list and record timestamp
6. Return list of violations

**Output**: List of violation dictionaries with alert details.

#### `_check_threshold(self, metrics, threshold)` (Line 110-130)
Performs the actual comparison operation.

**Supported Operators**:
- `>`: Greater than
- `<`: Less than
- `>=`: Greater than or equal
- `<=`: Less than or equal
- `==`: Equal to

**Returns**: Boolean indicating if threshold is violated.

---

### 3. SysSightAgent Class (Lines 132-418)

Main agent class that orchestrates all operations.

#### Initialization (`__init__`) (Lines 133-175)

Sets up the agent with configuration, creates HTTP session, initializes Flask app, and sets up default thresholds.

**Configuration Sources**:
1. Environment variables (with defaults)
2. System information (hostname, IP address)
3. Flask port for process serving

**Key Components Initialized**:
- `self.server_url`: Central server endpoint (default: `http://127.0.0.1:8000/metrics`)
- `self.interval`: Collection interval in seconds (default: 10)
- `self.auth_token`: Bearer token for authentication
- `self.hostname`: System hostname
- `self.flask_port`: Port for Flask server (default: 9090)
- `self.ip_address`: Primary IP address
- `self.metric_collectors`: Dictionary mapping metric names to collection functions
- `self.session`: `requests.Session` with persistent headers
- `self.flask_app`: Flask application instance
- `self.threshold_evaluator`: ThresholdEvaluator with default thresholds

**Metric Collectors Dictionary**:
```python
self.metric_collectors = {
    "cpu_percent": get_cpu_percent,
    "memory": get_memory_info,
    "disk": get_disk_info,
    "network": get_network_io,
    "load_average": get_load_average,
}
```

**Why Dictionary**: Allows dynamic iteration and easy addition/removal of metrics.

#### `_get_ip_address()` (Lines 177-188)
Determines the agent's IP address with multiple fallback strategies.

**Strategy 1**: Connect to a remote address (8.8.8.8) to determine outbound interface IP
- Uses UDP socket connection to Google DNS
- Returns the IP of the interface used for outbound traffic
- This is the most reliable method

**Strategy 2**: Use `gethostbyname(socket.gethostname())`
- Fallback if UDP connection fails
- May return loopback address (127.0.0.1) in some configurations

**Strategy 3**: Return "unknown"
- Final fallback if both methods fail
- Agent continues operating

**Why Multiple Strategies**: Ensures the agent can always provide an IP (or "unknown"), even in edge cases like containers or unconventional networking.

#### `_setup_flask_routes()` (Lines 190-198)
Configures Flask endpoints for serving process data.

**Route**: `GET /processes`

**Response**: JSON array of process dictionaries

**Error Handling**: Returns 500 status with error message if collection fails

#### `register_with_server(force=False)` (Lines 200-230)
Registers the agent with the central server.

**Purpose**: Informs the server about this agent's existence, IP address, and Flask port.

**Registration Frequency**: Every 5 minutes (300 seconds)

**Why Periodic Re-registration**:
- Server restarts would lose agent information
- Network changes (dynamic IP) would break communication
- New agents appear in the server's agent list

**Registration Payload**:
```python
{
    "hostname": self.hostname,
    "ip_address": self.ip_address,
    "port": self.flask_port
}
```

**Success Logging**: Prints confirmation message with details
**Failure Logging**: Prints error to stderr

#### `start_flask_server()` (Lines 232-239)
Starts Flask server in a daemon thread.

**Why Daemon Thread**: Automatically terminates when the main program exits, preventing orphaned processes.

**Threading Pattern**:
```python
def run_flask():
    self.flask_app.run(host='0.0.0.0', port=self.flask_port, debug=False, use_reloader=False)
    
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
```

**Host Binding**: `0.0.0.0` allows external access (server can reach agent)
**Debug**: Disabled for production use
**Reloader**: Disabled (incompatible with threading)

#### `fetch_thresholds_from_server()` (Lines 241-281)
Periodically fetches threshold configurations from the server.

**Frequency**: Every 20 seconds

**Why Periodic Fetch**:
- Allows dynamic threshold updates without restarting agents
- Supports centralized threshold management
- Enables A/B testing of threshold values

**Fetch Process**:
1. Checks time since last fetch (minimum 20 seconds)
2. Makes GET request to `/api/v1/thresholds`
3. Parses response JSON
4. Filters for enabled thresholds
5. Converts server format to agent format
6. Updates `threshold_evaluator.thresholds`
7. Logs update confirmation

**Error Handling**: Silently fails if server is unreachable, keeps using existing thresholds

**Rate Limiting Logging**: Only logs errors if threshold fetch has been failing for over 60 seconds

#### `send_alert(violation)` (Lines 283-307)
Sends an alert to the central server.

**Alert Payload**:
```python
{
    "hostname": self.hostname,
    "metric_name": violation['metric_name'],
    "metric_value": violation['metric_value'],
    "threshold_value": violation['threshold_value'],
    "severity": violation['severity'],
    "message": f"{violation['metric_name']} is {violation['metric_value']:.1f}% (threshold: {violation['threshold_value']:.1f}%)",
    "timestamp": datetime.utcnow().isoformat() + "Z"
}
```

**Timestamp Format**: ISO 8601 with 'Z' suffix (UTC)

**Why Non-blocking**: Failed alerts don't stop the agent's main loop

#### `collect_metrics()` (Lines 309-352)
Main metric collection orchestration method.

**Process**:
1. Determines IP address (with fallbacks)
2. Creates payload dictionary with metadata (hostname, timestamp, IP)
3. Iterates through metric collectors, calling each function
4. Evaluates thresholds against collected metrics
5. Sends alerts for any violations
6. Returns complete payload

**Error Handling**: Individual metric failures don't stop collection; failed metrics are set to `None`

**Threshold Evaluation**:
- Flattens nested metric data for evaluation
- Extracts CPU, memory, and disk percentages
- Passes to `threshold_evaluator.evaluate()`
- Sends alerts for each violation

#### `run()` (Lines 354-417)
Main execution loop of the agent.

**Startup Sequence**:
1. Print startup banner with configuration
2. Start Flask server in background thread
3. Force initial registration with server
4. Enter main loop

**Main Loop Activities**:
1. Record loop start time
2. Periodic re-registration (every 5 minutes)
3. Fetch threshold updates (every 20 seconds)
4. Collect all metrics
5. Log collected data to console
6. POST metrics to server
7. Handle HTTP and request exceptions
8. Calculate sleep duration based on elapsed time
9. Sleep until next interval

**Timing Strategy**:
```python
start_time = time.time()
# ... do work ...
elapsed_time = time.time() - start_time
sleep_duration = max(0, self.interval - elapsed_time)
time.sleep(sleep_duration)
```

This ensures the agent respects the collection interval even if work takes longer than expected.

**Signal Handling**: Handles `KeyboardInterrupt` (Ctrl+C) gracefully

**Exception Handling**:
- `HTTPError`: Server rejected data (logs server response)
- `RequestException`: Network or connection error (logs details)
- Continues running despite errors

---

## Threading Architecture

The agent uses threading to achieve concurrency while maintaining a simple event loop.

### Threading Usage

#### Thread 1: Main Agent Thread
**Responsibility**: Metric collection, server communication, threshold evaluation

**Operations**:
- Runs the main `run()` loop
- Collects metrics every N seconds
- Posts data to server
- Registers with server periodically
- Fetches threshold configurations
- Evaluates metrics against thresholds
- Sends alerts

**Why This Design**: Simple, predictable execution flow with a tight control loop.

#### Thread 2: Flask Server Thread (Daemon)
**Responsibility**: Serve process data to central server

**Operations**:
- Listens on `0.0.0.0:9090`
- Responds to `GET /processes` requests
- Returns JSON array of process information

**Why Daemon Thread**: Automatically terminates when the agent exits

**Why Background**: Doesn't block main metric collection loop

**Separation**: Server can query process list without interfering with metric collection

### Threading Benefits

1. **Non-blocking Flask Server**: Agent continues collecting metrics while serving process requests
2. **Concurrent Operations**: Multiple HTTP operations can happen simultaneously
3. **Resource Efficiency**: No forking overhead (unlike multiprocessing)
4. **Simplified State Management**: Shared memory access without locks
5. **Performance**: I/O operations don't block metric collection

### Threading Considerations

**Shared State**:
- `self.metric_collectors`: Read-only, thread-safe
- `self.session`: Thread-safe (requests.Session handles locking internally)
- `self.threshold_evaluator.thresholds`: May be modified by threshold fetch thread
- `self.sent_alerts`: Modified by threshold evaluation

**No Locking Required**: Operations are mostly independent with minimal shared state modification.

**Daemon Thread Safety**: Flask runs in daemon mode, ensuring clean shutdown.

---

## Data Flow

### Metric Collection Flow

```
Main Loop Start
    ↓
Check Time Thresholds
    ├─→ Register with Server (if 5 minutes elapsed)
    └─→ Fetch Thresholds (if 20 seconds elapsed)
    ↓
Collect Metrics
    ├─→ Get CPU Percent (1 second blocking)
    ├─→ Get Memory Info
    ├─→ Get Disk Info
    ├─→ Get Network I/O
    ├─→ Get Load Average
    └─→ Handle Exceptions for Each
    ↓
Evaluate Thresholds
    ├─→ Check Each Metric Against Thresholds
    ├─→ Deduplicate Alerts (10 second window)
    └─→ Send Alerts for Violations
    ↓
Post to Server
    ├─→ Create Payload
    ├─→ POST to /metrics
    └─→ Handle Response
    ↓
Sleep Until Next Interval
    ↓
Repeat
```

### Alert Generation Flow

```
Threshold Violation Detected
    ↓
Generate Alert Key
    ├─→ Format: {hostname}_{metric}_{severity}
    ↓
Check Deduplication
    ├─→ Has this alert been sent in last 10 seconds?
    ├─→ YES → Skip Alert
    └─→ NO → Continue
    ↓
Send Alert to Server
    ├─→ POST to /api/v1/alerts
    ├─→ Include: hostname, metric, value, severity
    └─→ Update Deduplication Timestamp
    ↓
Log Result
```

### Process Serving Flow

```
HTTP Request to GET /processes
    ↓
Flask Receives Request
    ↓
Call get_process_list()
    ├─→ Iterate All Processes
    ├─→ Extract PID, Name, CPU%, Memory%
    └─→ Handle Exceptions
    ↓
Return JSON Response
    ├─→ Serialize with jsonify
    └─→ Return to Client
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SYSSIGHT_SERVER_URL` | `http://127.0.0.1:8000/metrics` | Central server metrics endpoint |
| `SYSSIGHT_INTERVAL` | `10` | Collection interval in seconds |
| `SYSSIGHT_AUTH_TOKEN` | `your_secret_auth_token` | Bearer token for authentication |
| `SYSSIGHT_FLASK_PORT` | `9090` | Port for Flask process server |

### Default Thresholds

The agent ships with sensible default thresholds:

```python
[
    {'metric_name': 'cpu_percent', 'operator': '>', 'threshold_value': 80.0, 'severity': 'warning'},
    {'metric_name': 'cpu_percent', 'operator': '>', 'threshold_value': 95.0, 'severity': 'critical'},
    {'metric_name': 'mem_percent_used', 'operator': '>', 'threshold_value': 85.0, 'severity': 'warning'},
    {'metric_name': 'mem_percent_used', 'operator': '>', 'threshold_value': 95.0, 'severity': 'critical'},
    {'metric_name': 'disk_percent_used', 'operator': '>', 'threshold_value': 90.0, 'severity': 'warning'},
]
```

These can be overridden by fetching from the server.

---

## Error Handling

### Graceful Degradation Philosophy

The agent is designed to continue operating even when subsystems fail:

#### Network Failures
- **Symptom**: Server unreachable or network error
- **Behavior**: Logs error, continues collecting metrics, retries next interval
- **Reasoning**: Agent should never stop monitoring due to network issues

#### Metric Collection Failures
- **Symptom**: Individual metric function raises exception
- **Behavior**: Sets metric to `None` in payload, continues collecting other metrics
- **Reasoning**: One failing metric shouldn't stop collection of others

#### Process Access Failures
- **Symptom**: Permission denied or process terminated during iteration
- **Behavior**: Skips inaccessible processes, continues with accessible ones
- **Reasoning**: System processes may have different permissions

#### Threshold Evaluation Failures
- **Symptom**: Exception during threshold evaluation
- **Behavior**: Logs error, continues metric collection
- **Reasoning**: Threshold issues shouldn't stop monitoring

#### Flask Server Failures
- **Symptom**: Flask server cannot start
- **Behavior**: Logs error, main agent continues (only process serving affected)
- **Reasoning**: Primary function (metric collection) is unaffected

### Error Logging Strategy

**stdout**: Success messages, informational updates
**stderr**: Errors, warnings, failures

This allows users to separate success and error logs:
```bash
python agent.py > agent.log 2> agent.errors.log
```

### Timeout Management

All HTTP operations use 5-second timeouts to prevent hanging:
```python
timeout=5
```

### Retry Logic

The agent does NOT implement automatic retries. Instead:
- Periodic re-registration (every 5 minutes) handles server restarts
- Failed metrics are retried on the next collection cycle
- Alert deduplication prevents spam but allows eventual retry if issue persists

---

## Best Practices

### Security Considerations

1. **Authentication**: Uses Bearer token for server communication
2. **Port Binding**: Flask server binds to `0.0.0.0` (external access) - ensure firewall rules
3. **Process Access**: Requires appropriate permissions for process enumeration
4. **Error Messages**: Avoids exposing sensitive information in error logs

### Performance Optimizations

1. **Session Reuse**: `requests.Session` maintains persistent connections
2. **Attribute Filtering**: Process iteration uses filtered attributes
3. **Time-based Rate Limiting**: Registration and threshold fetch use time checks
4. **Deduplication**: Prevents alert spam
5. **Efficient Sleep**: Calculates actual sleep time based on elapsed work time

### Monitoring Best Practices

1. **Metric Frequency**: Balance between accuracy and overhead (default 10 seconds)
2. **Threshold Tuning**: Start with higher thresholds, adjust based on observed behavior
3. **Alert Spam Prevention**: 10-second window prevents excessive alerts
4. **Centralized Configuration**: Use server-side thresholds for easy management

---

## Future Enhancements

Potential improvements to the agent architecture:

1. **SSL/TLS Support**: Add HTTPS support for encrypted communication
2. **Compression**: Compress metric payloads for bandwidth efficiency
3. **Local Buffering**: Queue metrics if server is unreachable
4. **Custom Metric Plugins**: Support for user-defined metric collectors
5. **Health Check Endpoint**: Flask endpoint for agent health status
6. **Process Filtering**: Whitelist/blacklist process collection
7. **Historical Metrics**: Local caching of metrics for retrospective analysis
8. **Multiple Disk Support**: Monitor all disks, not just root
9. **GPU Metrics**: Add support for GPU utilization monitoring
10. **Container-Aware**: Special handling for containerized environments

---

## Troubleshooting

### Agent Fails to Start

**Symptoms**: Immediate exit or error on startup

**Common Causes**:
- Missing dependencies (`pip install -r requirements.txt`)
- Port 9090 already in use
- Permission issues accessing system metrics

**Solutions**:
- Install dependencies: `cd agent && source venv/bin/activate && pip install -r requirements.txt`
- Change Flask port: `export SYSSIGHT_FLASK_PORT=9091`
- Run with appropriate permissions

### Agent Connects but Server Not Receiving Data

**Symptoms**: Agent appears running but no data in server

**Common Causes**:
- Incorrect server URL configuration
- Network firewall blocking
- Authentication token mismatch

**Solutions**:
- Verify `SYSSIGHT_SERVER_URL` environment variable
- Test network connectivity: `curl http://SERVER_IP:8000`
- Verify auth token matches server configuration

### Excessive Alert Spam

**Symptoms**: Receiving too many alerts

**Solutions**:
- Check threshold values (may be too sensitive)
- Review deduplication window (currently 10 seconds)
- Adjust thresholds on server

### No Process Data Available

**Symptoms**: Server query to `/processes` returns empty

**Common Causes**:
- Flask server not running
- Firewall blocking port 9090
- Process permissions too restrictive

**Solutions**:
- Check Flask server is running (logs will show startup message)
- Verify firewall allows incoming connections on port 9090
- Run agent with appropriate permissions for process access

---

## Conclusion

The SysSight Agent is a well-architected, resilient monitoring solution designed for continuous operation with minimal resource overhead. Its threaded architecture enables concurrent HTTP serving and metric collection while maintaining simple state management. The agent's graceful degradation ensures it continues operating even under adverse conditions, making it suitable for production environments.

The combination of periodic registration, dynamic threshold fetching, and intelligent alert deduplication provides a robust foundation for distributed system monitoring while keeping the codebase maintainable and extensible.
