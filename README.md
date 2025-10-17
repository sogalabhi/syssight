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

### Useful Resources
- Zabbix Documentation: https://www.zabbix.com/documentation/current/manual
- Prometheus Documentation: https://prometheus.io/docs/introduction/overview/
- Grafana Documentation: https://grafana.com/docs/grafana/latest/
- Python psutil: https://psutil.readthedocs.io
- Linux /proc and /sys docs: https://man7.org/linux/man-pages/man5/proc.5.html
- WebSockets/SSE: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API and https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- FastAPI: https://fastapi.tiangolo.com/
- Charting: https://www.chartjs.org/ and https://recharts.org/
- Alerting guides: https://prometheus.io/docs/alerting/latest/alertmanager/ and https://www.zabbix.com/documentation/current/manual/config/triggers

---

## Getting Started

### Server (FastAPI + TimescaleDB/PostgreSQL)
From the repository root:
```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set your DB connection (TimescaleDB/PostgreSQL)
export DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/postgres

# Run the server from the REPO ROOT so imports resolve (note the path)
cd ..
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

### Agent (Linux metrics pusher)
In a separate terminal:
```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

export SYSSIGHT_SERVER_URL=http://127.0.0.1:8000/metrics
export SYSSIGHT_AUTH_TOKEN=your_secret_auth_token

python3 agent.py
```

---

## API Quick Test
- Interactive docs: `http://127.0.0.1:8000/docs`
- List hosts: `GET /api/v1/hosts`
- Latest metrics: `GET /api/v1/hosts/{host_id}/metrics/latest`
- Historical metrics (example):
```
GET /api/v1/hosts/{host_id}/metrics/historical/cpu_percent?start_time=2025-10-18T12:00:00Z&end_time=2025-10-18T13:00:00Z&step=1m
```

---

## Progress Summary

| Phase | Status |
|---|---|
| Phase 1 - Agent | Completed |
| Phase 2 - Server & Storage | Completed |
| Phase 3 - Dashboard | Completed |
| Phase 4 - Process Viewer | ⬜ Pending |
| Phase 5 - Alerting System | ⬜ Pending |
| Bonus 1 - Outbound Alerts | ⬜ Pending |
| Bonus 2 - Configurable Thresholds | ⬜ Pending |


