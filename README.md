## SysSight — Linux Task Manager

Task ID: SysSight

Domains: Systems Development, Web Development, Linux

Mentors: Shanjiv A (+91 8050030224), Suyash (+91 8583905686), Vatsal Jay Gandhi (+91 9409814992)

Difficulty: Expert

This is a GDG x Systems Task.

### Description

Build a Linux Task Manager with the following features:
- Each host runs a lightweight agent that continuously pushes system metrics (CPU, memory, disk, network, load average) to a central server.
- The central server stores historical metrics to generate charts over time.
- The dashboard shows real-time host metrics and allows users to fetch paginated process lists on demand (these lists are not stored).
- Implement an alerting system that alerts exceeding configurable resource thresholds and maintains an alert history that can be marked resolved.
- You can use any tech stack. No restrictions.

### Phases

#### Phase 1 - Linux Agent on the Host
Objective: Implement a Linux agent that continuously pushes host metrics.
- Collect system metrics periodically (CPU, memory, disk, network, load average).
- Push metrics continuously to the central server (HTTP or WebSocket).
- Ensure minimal CPU and network usage.
- Configurable push interval, server URL, and authentication.

#### Phase 2 - Central Server Setup & Metrics Storage
Objective: Set up a server to ingest and store metrics.
- Implement a server to receive metrics from multiple agents.
- Store historical metrics (time-series) for graphing.
- Expose APIs for:
  - Latest metrics per host.
  - Historical metrics for graphs over configurable time ranges.

#### Phase 3 - Frontend Dashboard & Graphs
Objective: Visualize live and historical metrics.
- Build a dashboard displaying each host’s metrics in real time.
- Show historical graphs for CPU, memory, disk, and network usage.
- Auto-refresh latest metrics for live updates.
- Include host selection to view individual metric graphs.

#### Phase 4 - On-Demand Paginated Process Viewer
Objective: Enable fetching and viewing current processes on demand.
- Agent gathers running processes (pid, name, cpu%, mem%) only when requested.
- Server exposes an API to request process lists for a host with pagination.
- Process lists are not persisted, only relayed to the dashboard.

#### Phase 5 - Alerting System
Objective: Generate and manage alerts.
- Agents detect exceeding host resource thresholds.
- Alerts are sent to the server containing host, metric, metric value, and timestamp.
- Server persists alerts with resolved/unresolved status.
- Dashboard allows viewing, resolving, and tracking alert history.

#### Bonus Phase 1 - Send Out Alerts
Objective: Send out alerts on email, Discord, etc.
- Send alerts as email/Discord/other notifications.
- When resolved, send a resolution notification as well.

#### Bonus Phase 2 - Configurable Thresholds
Objective: Allow dynamic configuration of resource limits.
- Implement per-host or per-process thresholds configurable from the server.
- Agents periodically fetch updated thresholds and apply them locally.

---

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **TimescaleDB** - PostgreSQL-based time-series database
- **SQLAlchemy** - Async ORM for database operations
- **Pydantic** - Data validation and settings management

### Agent
- **Python** - Core language
- **psutil** - System metrics collection
- **Flask** - Process server for on-demand data
- **requests** - HTTP client for metrics pushing

### Frontend
- **React** + **TypeScript** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Chart.js** - Chart library for visualizations

---

## Features

### Implemented Features

#### Phase 1 - Agent
- Collects system metrics (CPU, memory, disk, network, load average)
- Pushes metrics via HTTP every 10 seconds (configurable)
- Configurable server URL, auth token, and intervals
- Minimal resource footprint

#### Phase 2 - Server & Storage
- FastAPI server receives metrics from multiple agents
- TimescaleDB stores time-series historical data
- REST APIs for latest and historical metrics
- Agent registration system

#### Phase 3 - Dashboard
- Real-time metrics display with auto-refresh
- Interactive historical graphs (1h, 6h, 24h, custom ranges)
- Multi-host support with host selection
- Beautiful, responsive UI with Tailwind CSS
- Live status indicators (online/offline)

#### Phase 4 - Process Viewer
- On-demand process list fetching (not persisted)
- Paginated process table (10, 20, 50 items per page)
- Sortable by CPU%, memory%, PID, name
- Real-time process data from agents

#### Phase 5 - Alerting System
- **Agent-side threshold detection**:
  - CPU: >80% warning, >95% critical
  - Memory: >85% warning, >95% critical
  - Disk: >90% warning
- **Alert deduplication** (5-minute cooldown)
- **Server-side alert persistence** with status tracking
- **Dashboard alert management**:
  - Alert statistics dashboard
  - Color-coded severity badges (red=critical, yellow=warning, blue=info)
  - Filter by hostname, status, severity
  - Resolve alerts functionality
  - Alert history tracking

---

## Getting Started

### Prerequisites

1. **Docker** - For TimescaleDB database
2. **Python 3.8+** - For server and agent
3. **Node.js 16+** - For frontend dashboard
4. **stress** tool (optional) - For testing alerts

## Quick Start

If you've already set up the virtual environments and installed dependencies, use these commands:

```bash
# 1. Start Database
docker start syssight-timescale
# OR if you need to create it:
# docker run -d --name syssight-timescale -p 5432:5432 -e POSTGRES_PASSWORD=password timescale/timescaledb:latest-pg16

# 2. Start Server (in terminal 1)
cd /home/sogalabhi/coding/wec-task/syssight/server
source .venv/bin/activate
cd ..
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

# 3. Start Agent (in terminal 2) - run on each host
cd /home/sogalabhi/coding/wec-task/syssight/agent
source venv/bin/activate
python agent.py

# 4. Start Frontend (in terminal 3)
cd /home/sogalabhi/coding/wec-task/syssight/frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Testing the Alert System

### Alert Thresholds (Default)

The agent monitors the following thresholds:
- **CPU**: >80% (warning), >95% (critical)
- **Memory**: >85% (warning), >95% (critical)
- **Disk**: >90% (warning)

### CPU Stress Test

#### Install stress tool (if not already installed):
```bash
sudo apt-get install stress
```

#### Trigger CPU alerts:
```bash
# Stress all CPU cores for 60 seconds
stress --cpu $(nproc) --timeout 60s ## nproc = 16 in my case

# Check number of cores
nproc
```

**What happens:**
1. CPU usage will spike to ~95-100%
2. Agent detects threshold violation (>80% warning, >95% critical)
3. Agent sends alerts to server
4. Dashboard shows alert badges and notifications
5. Alerts appear in the Alerts page


### Verify Alerts

#### 1. Check Agent Output
You'll see:
```
Alert sent: cpu_percent = 97.5% (critical)
Alert sent: mem_percent_used = 87.2% (warning)
```

#### 2. Check Server Logs
You'll see:
```
Agent registered: sogalabhi -> 127.0.0.1:9090
INFO: 127.0.0.1:xxxxx - "POST /api/v1/alerts HTTP/1.1" 201 Created
```

#### 3. View in Dashboard
1. Navigate to **http://localhost:5173**
2. Dashboard page shows **alert badge** (e.g., "2 Active Alerts")
3. Click **"Alerts"** tab to see:
   - Alert statistics (active/resolved counts)
   - Alert table with color-coded severity
   - Filter by hostname, status, severity
   - **Resolve** button for active alerts

#### 4. Check via API
```bash
# Get all alerts
curl http://127.0.0.1:8000/api/v1/alerts | jq

# Get alert statistics
curl http://127.0.0.1:8000/api/v1/alerts/stats | jq

# Get only active alerts
curl "http://127.0.0.1:8000/api/v1/alerts?status=active" | jq

# Get critical alerts only
curl "http://127.0.0.1:8000/api/v1/alerts?severity=critical" | jq

# Resolve an alert
curl -X PATCH http://127.0.0.1:8000/api/v1/alerts/1/resolve | jq
```

### Alert Deduplication

The agent prevents spam by:
- Not sending duplicate alerts within **5 minutes**
- Using alert key: `{hostname}_{metric}_{severity}`
- Example: Same CPU warning won't be sent twice within 5 minutes

---

## API Quick Test
- Interactive docs: `http://127.0.0.1:8000/docs`
- List hosts: `GET /api/v1/hosts`
- Latest metrics: `GET /api/v1/hosts/{host_id}/metrics/latest`
- Historical metrics (example):`GET /api/v1/hosts/{host_id}/metrics/historical/cpu_percent?start_time=2025-10-18T12:00:00Z&end_time=2025-10-18T13:00:00Z&step=1m`
- List registered agents: `GET /api/v1/agents`
- Get process list: `GET /api/v1/hosts/{hostname}/processes?page=1&limit=10&sort_by=cpu_percent&sort_order=desc`
- Get alerts: `GET /api/v1/alerts?status=active&severity=critical`
- Alert stats: `GET /api/v1/alerts/stats`

---

## Progress Summary

| Phase | Status |
|---|---|
| Phase 1 - Agent | Completed |
| Phase 2 - Server & Storage | Completed |
| Phase 3 - Dashboard | Completed |
| Phase 4 - Process Viewer | Completed |
| Phase 5 - Alerting System | Completed |
| Bonus 1 - Outbound Alerts | ⬜ Pending |
| Bonus 2 - Configurable Thresholds | ⬜ Pending |


