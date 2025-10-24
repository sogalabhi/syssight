## SysSight — Linux Task Manager

A distributed system monitoring solution with real-time metrics, alerting, and Discord notifications.

### Tech Stack
- **Backend**: FastAPI, TimescaleDB, SQLAlchemy, Pydantic
- **Agent**: Python, psutil, Flask
- **Frontend**: React + TypeScript, Vite, Tailwind CSS, Chart.js

---

## Features

### Core Functionality
- **Agent**: Collects system metrics (CPU, memory, disk, network, load) every 10s
- **Server**: TimescaleDB time-series storage with REST APIs
- **Dashboard**: Real-time metrics display with interactive historical graphs
- **Process Viewer**: On-demand paginated process lists (sortable, not persisted)
- **Alerting**: Threshold detection, persistence, and management UI
- **Discord Notifications**: Rich embed alerts with color coding
- **Configurable Thresholds**: Web UI for dynamic threshold management (updates every 20s)

### Default Thresholds
- CPU: >80% warning, >95% critical
- Memory: >85% warning, >95% critical  
- Disk: >90% warning

---

## Quick Start

### Prerequisites
- Docker (TimescaleDB)
- Python 3.8+
- Node.js 16+

### Setup & Run

```bash
# 1. Database
docker run -d --name syssight-timescale -p 5432:5432 \
  -e POSTGRES_PASSWORD=password timescale/timescaledb:latest-pg16

# 2. Server (terminal 1)
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd .. && uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

# 3. Agent (terminal 2)
cd agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python agent.py

# 4. Frontend (terminal 3)
cd frontend
npm install && npm run dev
```

**Access**: http://localhost:5173 (Frontend) | http://localhost:8000/docs (API)

### Quick Restart (if already setup)

```bash
# Terminal 1: Server
docker start syssight-timescale
cd server && source .venv/bin/activate && cd ..
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Agent
cd agent && source venv/bin/activate && python agent.py

# Terminal 3: Frontend
cd frontend && npm run dev
```

---

## Configuration

### Discord Notifications

Create `.env` in project root:
```bash
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
SYSSIGHT_AUTH_TOKEN=your_secret_auth_token
```

**Setup**:
1. Create bot at https://discord.com/developers/applications
2. Copy bot token
3. Invite bot with `Send Messages` and `Embed Links` permissions
4. Right-click channel → Copy Channel ID (enable Developer Mode)
5. Restart server

### Configurable Thresholds

1. Navigate to **Alerts** page
2. Edit threshold values in **Threshold Configuration** section
3. Click **Save Changes** (agents update within 20s)
4. Use **Reset to Defaults** to restore original values

**API**:
```bash
# Get thresholds
curl http://127.0.0.1:8000/api/v1/thresholds

# Reset to defaults
curl -X POST http://127.0.0.1:8000/api/v1/thresholds/reset
```

---

## Testing Alerts

```bash
# Install stress tool
sudo apt-get install stress

# Trigger CPU alerts (60 seconds)
stress --cpu $(nproc) --timeout 60s

# Check alerts
curl http://127.0.0.1:8000/api/v1/alerts?status=active
```

**Expected behavior**:
- Agent logs: `Alert sent: cpu_percent = 95.0% (warning)`
- Dashboard: Alert badges and notifications
- Discord: Rich embed notifications (if configured)

---

## API Reference

**Interactive docs**: http://127.0.0.1:8000/docs

### Key Endpoints
```bash
# Hosts & Metrics
GET  /api/v1/hosts
GET  /api/v1/hosts/{host_id}/metrics/latest
GET  /api/v1/hosts/{host_id}/metrics/historical/{metric_type}

# Processes
GET  /api/v1/hosts/{hostname}/processes?page=1&limit=10

# Alerts
GET  /api/v1/alerts?status=active&severity=critical
GET  /api/v1/alerts/stats
PATCH /api/v1/alerts/{alert_id}/resolve

# Thresholds
GET  /api/v1/thresholds
PUT  /api/v1/thresholds
POST /api/v1/thresholds/reset

# Agents
GET  /api/v1/agents
POST /api/v1/agents/register
```

---

## Agent Registration

Agents automatically register on startup and re-register every 5 minutes.

**Verify registration**:
```bash
curl http://127.0.0.1:8000/api/v1/agents
```

**Note**: Registry is in-memory. Restart server = agents re-register automatically.

---

## Architecture

```
┌─────────────┐      HTTP/10s     ┌──────────────┐
│   Agent     │ ────────────────> │    Server    │
│  (psutil)   │                   │  (FastAPI)   │
└─────────────┘                   └──────┬───────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │ TimescaleDB  │
                                  └──────────────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │  Dashboard   │
                                  │ (React + TS) │
                                  └──────────────┘
```

**Data Flow**:
1. Agent collects metrics → POST to server every 10s
2. Server stores in TimescaleDB (hypertable)
3. Dashboard fetches via REST APIs
4. Alerts trigger → Discord notifications
5. Thresholds configurable via UI → agents fetch every 20s

---

## Project Status

| Phase | Status |
|---|---|
| Phase 1 - Agent | Completed |
| Phase 2 - Server & Storage | Completed |
| Phase 3 - Dashboard | Completed |
| Phase 4 - Process Viewer | Completed |
| Phase 5 - Alerting System | Completed |
| Bonus 1 - Discord Notifications | Completed |
| Bonus 2 - Configurable Thresholds | Completed |

---

## Development

**Backend**:
```bash
cd server
source .venv/bin/activate
uvicorn server.app:app --reload
```

**Frontend**:
```bash
cd frontend
npm run dev
```

**Agent**:
```bash
cd agent
source venv/bin/activate
python agent.py
```

---

Built for WEC Systems Task | GDG x Systems Development
