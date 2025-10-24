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

#### Bonus Phase 1 - Discord Notifications
- **Real-time Discord webhook notifications**:
  - Rich embed formatting with color coding
  - Alert triggered notifications with full details
  - Alert resolution notifications with duration
  - Configurable via environment variable
  - Graceful fallback if webhook not configured

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

**Agent Registration:**

The agent automatically registers with the server when it starts. You should see:
```
Registered with server: sogalabhi -> 127.0.0.1:9090
```

The agent re-registers every 5 minutes to handle server restarts. To verify registration:
```bash
# Check registered agents
curl http://127.0.0.1:8000/api/v1/agents

# Test process viewer (requires registered agent)
curl http://127.0.0.1:8000/api/v1/hosts/sogalabhi/processes?page=1&limit=5
```

**Important Notes:**
- The agent registry is stored in **memory** (not database)
- If you restart the **server**, agents will automatically re-register within 5 minutes
- If you restart the **agent**, it registers immediately on startup
- Process viewer requires agent registration to fetch live process data

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
stress --cpu 16 --timeout 60s ## nproc = 16 in my case

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

## Discord Alert Notifications

### Overview

SysSight can send real-time alert notifications to Discord using a Discord bot. When alerts are triggered or resolved, formatted embed messages are automatically posted to your Discord channel.

### Features

- **Rich Embed Formatting**: Color-coded messages based on severity
  - 🔴 Critical: Red
  - 🟠 Warning: Orange
  - 🔵 Info: Blue
  - 🟢 Resolved: Green
- **Detailed Information**: Includes hostname, metric name, values, thresholds, and timestamps
- **Resolution Notifications**: Automatic notifications when alerts are resolved
- **Duration Tracking**: Shows how long an alert was active
- **Bot-based Integration**: Uses Discord bot API for reliable message delivery

### Setup Instructions

#### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name (e.g., "SysSight Alerts")
3. Go to the **Bot** section in the left sidebar
4. Click **Add Bot** (or **Reset Token** if bot already exists)
5. Click **Copy** to copy your bot token
6. Under **Privileged Gateway Intents**, you don't need any special intents enabled

#### 2. Invite Bot to Your Server

1. In the Discord Developer Portal, go to **OAuth2** → **URL Generator**
2. Select scopes: `bot`
3. Select bot permissions: `Send Messages`, `Embed Links`
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

#### 3. Get Your Channel ID

1. In Discord, enable **Developer Mode** (User Settings → Advanced → Developer Mode)
2. Right-click the channel where you want alerts
3. Click **Copy Channel ID**
4. Save this ID (e.g., `1385676035189637231`)

#### 4. Configure Environment Variables

Set the `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` environment variables:

**Option A: Export in terminal (temporary)**
```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
export DISCORD_CHANNEL_ID="1385676035189637231"
```

**Option B: Add to .env file (persistent) - RECOMMENDED**
Create a `.env` file in the project root:
```bash
cd /home/sogalabhi/coding/wec-task/syssight
cat > .env << 'EOF'
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=1385676035189637231
EOF
```

**Option C: Add to shell profile (system-wide)**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export DISCORD_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
echo 'export DISCORD_CHANNEL_ID="1385676035189637231"' >> ~/.bashrc
source ~/.bashrc
```

#### 5. Install Dependencies and Restart the Server

Install the new discord.py dependency:
```bash
cd /home/sogalabhi/coding/wec-task/syssight/server
source .venv/bin/activate
pip install discord.py==2.4.0
```

Then restart the server:
```bash
cd /home/sogalabhi/coding/wec-task/syssight
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
🤖 Discord bot starting in background...
Discord bot connected as YourBotName#1234
Discord channel found: your-channel-name
```

### Testing Discord Notifications

#### Trigger an Alert
```bash
# Stress CPU to trigger alerts
stress --cpu $(nproc) --timeout 60s
```

You should see a Discord message like:

```
🚨 Alert Triggered: CRITICAL

CPU usage on sogalabhi has exceeded threshold

🖥️ Hostname: sogalabhi
📊 Metric: cpu_percent
📈 Current Value: 97.50
⚠️ Threshold: 95.00
🔴 Severity: CRITICAL
🕒 Triggered At: 2025-10-24 12:34:56 UTC

Alert ID: 1 | SysSight Monitoring
```

#### Resolve the Alert

From the dashboard or via API:
```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/alerts/1/resolve
```

You'll receive a resolution notification:

```
Alert Resolved

Alert for cpu_percent on sogalabhi has been resolved.

🖥️ Hostname: sogalabhi
📊 Metric: cpu_percent
🔴 Original Severity: CRITICAL
🕒 Triggered At: 2025-10-24 12:34:56 UTC
Resolved At: 2025-10-24 12:40:12 UTC
⏱️ Duration: 0:05:16

Alert ID: 1 | Resolved by: system | SysSight Monitoring
```

### Troubleshooting

**No notifications appearing?**
1. Check server logs for bot connection status:
   ```
   🤖 Discord bot starting in background...
   Discord bot connected as YourBotName#1234
   Discord channel found: your-channel-name
   ```
2. Verify environment variables are set:
   ```bash
   echo $DISCORD_BOT_TOKEN
   echo $DISCORD_CHANNEL_ID
   ```
3. Ensure the bot has **Send Messages** and **Embed Links** permissions in the channel
4. Check if bot is online in your Discord server's member list
5. Verify the channel ID is correct (right-click channel → Copy Channel ID)

**Bot not connecting?**
- Check if bot token is valid (tokens expire if reset in Developer Portal)
- Ensure bot has been invited to your server
- Check for error messages in server logs:
  ```
  ❌ Failed to start Discord bot: Improper token has been passed
  ```

**Bot connected but no messages?**
- Verify channel permissions (bot needs "Send Messages" and "Embed Links")
- Check if the channel ID matches your intended channel
- Look for messages like:
  ```
  ⚠️  Discord bot not ready yet. Skipping notification.
  ```

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
| Bonus 1 - Outbound Alerts (Discord) | Completed |
| Bonus 2 - Configurable Thresholds | ⬜ Pending |


