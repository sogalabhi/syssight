# SysSight API Endpoints Reference

Complete reference for all API endpoints in the SysSight monitoring system.

## Table of Contents
1. [Agent Endpoints](#agent-endpoints)
2. [Server Endpoints](#server-endpoints)
3. [Authentication](#authentication)
4. [Request/Response Formats](#requestresponse-formats)

---

## Agent Endpoints

The agent runs on **port 9090** by default and exposes a minimal Flask API for process management.

### Base URL
```
http://<agent-ip>:9090
```

---

### 1. GET /processes

Returns the list of running processes on the agent's host.

**Method**: `GET`  
**URL**: `/processes`  
**Auth**: None  
**File**: `agent/agent.py` (lines 192-198)

#### Request
```http
GET /processes HTTP/1.1
Host: 192.168.1.100:9090
```

#### Response
**Status Code**: `200 OK`

```json
[
  {
    "pid": 1234,
    "name": "python",
    "cpu_percent": 5.2,
    "memory_percent": 2.1
  },
  {
    "pid": 5678,
    "name": "firefox",
    "cpu_percent": 8.5,
    "memory_percent": 15.3
  }
]
```

#### Response Fields
- `pid` (integer): Process ID
- `name` (string): Process name
- `cpu_percent` (float): CPU usage percentage (rounded to 2 decimals)
- `memory_percent` (float): Memory usage percentage (rounded to 2 decimals)

#### Notes
- Handles permission errors gracefully (skips inaccessible processes)
- Processes are sorted client-side by the server
- No pagination (returns all processes)

---

## Server Endpoints

The server runs on **port 8000** by default and provides the main API for metrics, alerts, and configuration.

### Base URL
```
http://localhost:8000
```

### API Prefix
```
/api/v1
```

---

## Server: Metrics Endpoints

### 1. POST /metrics

Receives and stores metrics from agents.

**Method**: `POST`  
**URL**: `/metrics`  
**Auth**: Bearer token required  
**File**: `server/app.py` (line 140)

#### Request Headers
```http
Authorization: Bearer your_secret_auth_token
Content-Type: application/json
```

#### Request Body
```json
{
  "hostname": "server-01",
  "timestamp": "2024-01-15T10:30:00Z",
  "ip_address": "192.168.1.100",
  "cpu_percent": 45.5,
  "memory": {
    "total_gb": 16.0,
    "available_gb": 8.5,
    "percent_used": 47.0
  },
  "disk": {
    "total_gb": 500.0,
    "used_gb": 300.0,
    "free_gb": 200.0,
    "percent_used": 60.0
  },
  "network": {
    "bytes_sent": 1024000,
    "bytes_received": 2048000
  },
  "load_average": {
    "1m": 1.5,
    "5m": 1.2,
    "15m": 0.8,
    "1m_normalized": 0.375,
    "5m_normalized": 0.3,
    "15m_normalized": 0.2
  }
}
```

#### Response
**Status Code**: `201 Created`

```json
{
  "status": "success",
  "message": "Metric ID 1234 saved"
}
```

---

### 2. GET /api/v1/hosts

List all monitored hosts with their status and last seen timestamp.

**Method**: `GET`  
**URL**: `/api/v1/hosts`  
**Auth**: None  
**File**: `server/api_routes.py` (line 29)

#### Query Parameters
None

#### Response
**Status Code**: `200 OK`

```json
[
  {
    "host_id": "server-01",
    "hostname": "server-01",
    "ip_address": "192.168.1.100",
    "last_seen": "2024-01-15T10:30:00Z",
    "status": "online"
  },
  {
    "host_id": "server-02",
    "hostname": "server-02",
    "ip_address": "192.168.1.101",
    "last_seen": "2024-01-15T10:25:00Z",
    "status": "offline"
  }
]
```

#### Response Fields
- `host_id` (string): Host identifier (same as hostname)
- `hostname` (string): Hostname
- `ip_address` (string): IP address or "unknown"
- `last_seen` (string): ISO 8601 timestamp of last metric
- `status` (string): "online" or "offline" (based on 5-minute window)

---

### 3. GET /api/v1/hosts/{host_id}/metrics/latest

Get the latest metrics for a specific host.

**Method**: `GET`  
**URL**: `/api/v1/hosts/{host_id}/metrics/latest`  
**Auth**: None  
**File**: `server/api_routes.py` (line 73)

#### Path Parameters
- `host_id` (string): Host identifier

#### Response
**Status Code**: `200 OK`

```json
{
  "host_id": "server-01",
  "timestamp": "2024-01-15T10:30:00Z",
  "cpu_percent": 45.5,
  "memory_percent": 47.0,
  "disk_usage": {
    "/": {
      "percent": 60.0
    }
  },
  "network": {
    "bytes_sent": 1024000,
    "bytes_recv": 2048000
  },
  "load_average": [1.5, 1.2, 0.8]
}
```

**Status Code**: `404 Not Found`
```json
{
  "detail": "Host 'server-01' not found"
}
```

---

### 4. GET /api/v1/hosts/{host_id}/metrics/historical/{metric_type}

Get historical time-series metrics with aggregation for graphing.

**Method**: `GET`  
**URL**: `/api/v1/hosts/{host_id}/metrics/historical/{metric_type}`  
**Auth**: None  
**File**: `server/api_routes.py` (line 118)

#### Path Parameters
- `host_id` (string): Host identifier
- `metric_type` (string): One of: `cpu_percent`, `mem_percent_used`, `disk_percent_used`, `net_bytes_sent`, `net_bytes_received`, `load_1m`, `load_5m`, `load_15m`

#### Query Parameters
- `start_time` (string, required): Start time in ISO 8601 format (e.g., "2024-01-15T00:00:00Z")
- `end_time` (string, required): End time in ISO 8601 format (e.g., "2024-01-15T23:59:59Z")
- `step` (string, optional): Aggregation step. Default: `"1m"`. Allowed: `"1m"`, `"5m"`, `"1h"`, `"1d"`

#### Example Request
```http
GET /api/v1/hosts/server-01/metrics/historical/cpu_percent?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z&step=1h HTTP/1.1
```

#### Response
**Status Code**: `200 OK`

```json
{
  "metric_type": "cpu_percent",
  "values": [
    [1705276800, 45.5],
    [1705280400, 50.2],
    [1705284000, 48.8]
  ]
}
```

**Response Fields**:
- `metric_type` (string): The requested metric type
- `values` (array): Array of [timestamp, value] pairs
  - `timestamp` (integer): Unix timestamp
  - `value` (float): Averaged metric value for the time bucket

**Error Responses**:
- `400 Bad Request`: Invalid metric_type or timestamp format
- `404 Not Found`: Host does not exist

---

## Server: Agent Management Endpoints

### 5. POST /api/v1/agents/register

Register an agent with the server.

**Method**: `POST`  
**URL**: `/api/v1/agents/register`  
**Auth**: None  
**File**: `server/api_routes.py` (line 212)

#### Request Body
```json
{
  "hostname": "server-01",
  "ip_address": "192.168.1.100",
  "port": 9090
}
```

#### Response
**Status Code**: `200 OK`

```json
{
  "status": "success",
  "message": "Agent server-01 registered at 192.168.1.100:9090"
}
```

**Status Code**: `400 Bad Request`
```json
{
  "detail": "Missing required fields: hostname, ip_address, port"
}
```

#### Notes
- Agents automatically register on startup
- Re-register every 5 minutes to handle server restarts
- Registry stored in-memory (lost on server restart)

---

### 6. GET /api/v1/agents

List all registered agents.

**Method**: `GET`  
**URL**: `/api/v1/agents`  
**Auth**: None  
**File**: `server/api_routes.py` (line 239)

#### Response
**Status Code**: `200 OK`

```json
{
  "agents": {
    "server-01": "192.168.1.100:9090",
    "server-02": "192.168.1.101:9090"
  },
  "count": 2
}
```

---

### 7. GET /api/v1/hosts/{hostname}/processes

Get paginated process list for a specific host (proxies to agent).

**Method**: `GET`  
**URL**: `/api/v1/hosts/{hostname}/processes`  
**Auth**: None  
**File**: `server/api_routes.py` (line 249)

#### Path Parameters
- `hostname` (string): Hostname of the agent

#### Query Parameters
- `page` (integer, optional): Page number. Default: `1`, Minimum: `1`
- `limit` (integer, optional): Items per page. Default: `10`, Min: `1`, Max: `100`
- `sort_by` (string, optional): Sort field. Default: `"cpu_percent"`. Allowed: `"cpu_percent"`, `"memory_percent"`, `"pid"`, `"name"`
- `sort_order` (string, optional): Sort order. Default: `"desc"`. Allowed: `"asc"`, `"desc"`

#### Example Request
```http
GET /api/v1/hosts/server-01/processes?page=1&limit=50&sort_by=cpu_percent&sort_order=desc HTTP/1.1
```

#### Response
**Status Code**: `200 OK`

```json
{
  "processes": [
    {
      "pid": 1234,
      "name": "python",
      "cpu_percent": 45.2,
      "memory_percent": 15.3
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "total_pages": 3
}
```

**Status Code**: `404 Not Found`
```json
{
  "detail": "Agent 'server-01' not registered. Available agents: ['server-02']"
}
```

#### Notes
- Server fetches all processes from agent, then paginates client-side
- Sorting and pagination performed on server (not in agent or database)

---

## Server: Alert Management Endpoints

### 8. POST /api/v1/alerts

Create a new alert (called by agents).

**Method**: `POST`  
**URL**: `/api/v1/alerts`  
**Auth**: None  
**File**: `server/api_routes.py` (line 316)

#### Request Body
```json
{
  "hostname": "server-01",
  "metric_name": "cpu_percent",
  "metric_value": 85.5,
  "threshold_value": 80.0,
  "severity": "warning",
  "message": "cpu_percent is 85.5% (threshold: 80.0%)",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Response
**Status Code**: `200 OK`

```json
{
  "status": "created",
  "alert_id": 123
}
```

**OR**

```json
{
  "status": "updated",
  "alert_id": 123
}
```

#### Notes
- Checks for existing active alerts to prevent duplicates
- Sends Discord notification for new alerts
- Updates timestamp for existing alerts (to track ongoing violations)

---

### 9. GET /api/v1/alerts

List alerts with optional filtering and pagination.

**Method**: `GET`  
**URL**: `/api/v1/alerts`  
**Auth**: None  
**File**: `server/api_routes.py` (line 367)

#### Query Parameters
- `hostname` (string, optional): Filter by hostname
- `status` (string, optional): Filter by status. Allowed: `"active"`, `"resolved"`, `"acknowledged"`
- `severity` (string, optional): Filter by severity. Allowed: `"info"`, `"warning"`, `"critical"`
- `page` (integer, optional): Page number. Default: `1`, Minimum: `1`
- `limit` (integer, optional): Items per page. Default: `50`, Min: `1`, Max: `100`

#### Example Request
```http
GET /api/v1/alerts?hostname=server-01&status=active&page=1&limit=20 HTTP/1.1
```

#### Response
**Status Code**: `200 OK`

```json
{
  "alerts": [
    {
      "id": 123,
      "hostname": "server-01",
      "metric_name": "cpu_percent",
      "metric_value": 85.5,
      "threshold_value": 80.0,
      "severity": "warning",
      "status": "active",
      "message": "cpu_percent is 85.5% (threshold: 80.0%)",
      "triggered_at": "2024-01-15T10:30:00Z",
      "resolved_at": null,
      "resolved_by": null
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3
}
```

---

### 10. PATCH /api/v1/alerts/{alert_id}/resolve

Mark an alert as resolved.

**Method**: `PATCH`  
**URL**: `/api/v1/alerts/{alert_id}/resolve`  
**Auth**: None  
**File**: `server/api_routes.py` (line 428)

#### Path Parameters
- `alert_id` (integer): Alert ID

#### Response
**Status Code**: `200 OK`

```json
{
  "status": "success",
  "message": "Alert 123 resolved"
}
```

**Status Code**: `404 Not Found`
```json
{
  "detail": "Alert not found"
}
```

**Status Code**: `400 Bad Request`
```json
{
  "detail": "Alert already resolved"
}
```

#### Notes
- Sets `resolved_at` timestamp
- Sets `resolved_by` to "system" (would be user in real app)
- Sends Discord resolution notification

---

### 11. GET /api/v1/alerts/stats

Get alert statistics summary.

**Method**: `GET`  
**URL**: `/api/v1/alerts/stats`  
**Auth**: None  
**File**: `server/api_routes.py` (line 463)

#### Response
**Status Code**: `200 OK`

```json
{
  "active_count": 15,
  "resolved_count": 120,
  "by_severity": {
    "info": 0,
    "warning": 10,
    "critical": 5
  }
}
```

#### Response Fields
- `active_count` (integer): Number of active alerts
- `resolved_count` (integer): Number of resolved alerts
- `by_severity` (object): Count of active alerts by severity

---

## Server: Threshold Configuration Endpoints

### 12. GET /api/v1/thresholds

Get all global threshold configurations.

**Method**: `GET`  
**URL**: `/api/v1/thresholds`  
**Auth**: None  
**File**: `server/api_routes.py` (line 510)

#### Response
**Status Code**: `200 OK`

```json
{
  "thresholds": [
    {
      "id": 1,
      "metric_name": "cpu_percent",
      "operator": ">",
      "threshold_value": 80.0,
      "severity": "warning",
      "enabled": true
    },
    {
      "id": 2,
      "metric_name": "cpu_percent",
      "operator": ">",
      "threshold_value": 95.0,
      "severity": "critical",
      "enabled": true
    }
  ]
}
```

#### Notes
- Returns hardcoded defaults if database is empty
- Only returns global thresholds (hostname = NULL)
- Used by agents to fetch threshold configuration

---

### 13. PUT /api/v1/thresholds

Update all global threshold configurations.

**Method**: `PUT`  
**URL**: `/api/v1/thresholds`  
**Auth**: None  
**File**: `server/api_routes.py` (line 546)

#### Request Body
```json
{
  "thresholds": [
    {
      "metric_name": "cpu_percent",
      "operator": ">",
      "threshold_value": 75.0,
      "severity": "warning",
      "enabled": true
    },
    {
      "metric_name": "mem_percent_used",
      "operator": ">",
      "threshold_value": 80.0,
      "severity": "warning",
      "enabled": true
    }
  ]
}
```

#### Response
**Status Code**: `200 OK`

```json
{
  "thresholds": [
    {
      "id": 1,
      "metric_name": "cpu_percent",
      "operator": ">",
      "threshold_value": 75.0,
      "severity": "warning",
      "enabled": true
    },
    {
      "id": 2,
      "metric_name": "mem_percent_used",
      "operator": ">",
      "threshold_value": 80.0,
      "severity": "warning",
      "enabled": true
    }
  ]
}
```

#### Notes
- Replaces all existing global thresholds
- Deletes old thresholds before inserting new ones
- Agents will pick up changes within 20 seconds

---

### 14. POST /api/v1/thresholds/reset

Reset global thresholds to hardcoded defaults.

**Method**: `POST`  
**URL**: `/api/v1/thresholds/reset`  
**Auth**: None  
**File**: `server/api_routes.py` (line 597)

#### Response
**Status Code**: `200 OK`

```json
{
  "thresholds": [
    {
      "id": 1,
      "metric_name": "cpu_percent",
      "operator": ">",
      "threshold_value": 80.0,
      "severity": "warning",
      "enabled": true
    },
    {
      "id": 2,
      "metric_name": "cpu_percent",
      "operator": ">",
      "threshold_value": 95.0,
      "severity": "critical",
      "enabled": true
    },
    {
      "id": 3,
      "metric_name": "mem_percent_used",
      "operator": ">",
      "threshold_value": 85.0,
      "severity": "warning",
      "enabled": true
    },
    {
      "id": 4,
      "metric_name": "mem_percent_used",
      "operator": ">",
      "threshold_value": 95.0,
      "severity": "critical",
      "enabled": true
    },
    {
      "id": 5,
      "metric_name": "disk_percent_used",
      "operator": ">",
      "threshold_value": 90.0,
      "severity": "warning",
      "enabled": true
    }
  ]
}
```

#### Default Thresholds
- CPU: >80% (warning), >95% (critical)
- Memory: >85% (warning), >95% (critical)
- Disk: >90% (warning)

---

## Authentication

### Server Endpoints Requiring Auth

- `POST /metrics`: Requires Bearer token

### Server Endpoints Without Auth

All other server endpoints are publicly accessible (for internal network use).

### Agent Endpoints

- No authentication required

### Setting Auth Token

**Environment Variable**: `SYSSIGHT_AUTH_TOKEN`

**Default**: `"your_secret_auth_token"`

**Usage**:
```bash
export SYSSIGHT_AUTH_TOKEN="my_secret_token"
```

### Request Format
```http
Authorization: Bearer my_secret_token
```

---

## Request/Response Formats

### Timestamp Format

**ISO 8601 with Z suffix**: `2024-01-15T10:30:00Z`

All timestamps are in UTC.

### Pagination

Standard pagination across endpoints:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "total_pages": 5
}
```

### Error Format

All errors follow this structure:
```json
{
  "detail": "Error message here"
}
```

**Common Status Codes**:
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Complete Endpoint List

### Agent Endpoints (Port 9090)
1. **GET /processes** - List processes

### Server Endpoints (Port 8000)
1. **POST /metrics** - Store metrics (auth required)
2. **GET /api/v1/hosts** - List hosts
3. **GET /api/v1/hosts/{id}/metrics/latest** - Latest metrics
4. **GET /api/v1/hosts/{id}/metrics/historical/{type}** - Historical metrics
5. **POST /api/v1/agents/register** - Register agent
6. **GET /api/v1/agents** - List agents
7. **GET /api/v1/hosts/{hostname}/processes** - List processes
8. **POST /api/v1/alerts** - Create alert
9. **GET /api/v1/alerts** - List alerts
10. **PATCH /api/v1/alerts/{id}/resolve** - Resolve alert
11. **GET /api/v1/alerts/stats** - Alert statistics
12. **GET /api/v1/thresholds** - Get thresholds
13. **PUT /api/v1/thresholds** - Update thresholds
14. **POST /api/v1/thresholds/reset** - Reset thresholds

**Total**: 1 Agent endpoint + 14 Server endpoints = **15 endpoints**

---

## Interactive API Documentation

FastAPI provides automatic API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## References

- **Agent Routes**: `agent/agent.py`
- **Server Routes**: `server/api_routes.py`, `server/app.py`
- **Database Models**: `server/models.py`
- **Pydantic Models**: `server/pydantic_models.py`
- **Full Documentation**: See other `.md` files in project root

