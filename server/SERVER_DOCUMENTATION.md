# SysSight Server - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Files and Structure](#files-and-structure)
4. [Dependencies](#dependencies)
5. [Core Components](#core-components)
6. [Database Schema](#database-schema)
7. [Async Architecture](#async-architecture)
8. [API Endpoints](#api-endpoints)
9. [Integration Points](#integration-points)
10. [Data Flow](#data-flow)
11. [Configuration](#configuration)
12. [Error Handling](#error-handling)
13. [Security](#security)
14. [Best Practices](#best-practices)

---

## Overview

The SysSight Server is a FastAPI-based central monitoring system that receives, stores, and manages metrics from distributed agents. It provides a RESTful API for real-time monitoring, historical data analysis, alert management, and threshold configuration.

### Key Responsibilities
- **Metric Ingestion**: Receive and validate metrics from agents
- **Time-Series Storage**: Store metrics in TimescaleDB for efficient time-series queries
- **Alert Management**: Track and manage system alerts with state management
- **Threshold Configuration**: Dynamically configure monitoring thresholds
- **Agent Registry**: Maintain registry of active agents and their connection details
- **Process Proxy**: Proxy process list requests from agents
- **Discord Integration**: Send real-time notifications to Discord channels
- **CORS Support**: Enable cross-origin requests from frontend

### Technology Stack
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **TimescaleDB**: PostgreSQL extension optimized for time-series data
- **AsyncIO**: Asynchronous I/O for high performance
- **Discord.py**: Discord bot integration for notifications

---

## Architecture

The server follows a layered, asynchronous architecture:

1. **Presentation Layer**: FastAPI routes and middleware
2. **Business Logic Layer**: API route handlers
3. **Data Access Layer**: SQLAlchemy models and database connections
4. **External Integrations**: Discord bot and agent communication

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SysSight Server                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              FastAPI Application                       │   │
│  │  • CORS Middleware                                     │   │
│  │  • Startup Event Handler                              │   │
│  │  • Authentication Middleware                          │   │
│  └────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              API Routes (api_routes.py)                │   │
│  │                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │   Hosts      │  │   Agents     │  │   Alerts    │ │   │
│  │  │  Endpoints   │  │  Registry    │  │ Management  │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │   │
│  │                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │  Historical │  │  Processes   │  │  Thresholds  │ │   │
│  │  │   Metrics   │  │    Proxy     │  │  Config      │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │   │
│  └────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │         Database Layer (SQLAlchemy Async)              │   │
│  │  • Metric Model                                        │   │
│  │  • Alert Model                                         │   │
│  │  • ThresholdConfig Model                               │   │
│  │  • Process Model (for future use)                     │   │
│  └────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              TimescaleDB / PostgreSQL                 │   │
│  │  • Metrics Table (Hypertable)                         │   │
│  │  • Alerts Table                                        │   │
│  │  • Threshold Configs Table                            │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │         Discord Bot (Background Thread)                │   │
│  │  • Send Alert Notifications                            │   │
│  │  • Send Resolution Notifications                      │   │
│  │  • Rich Embed Formatting                              │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │         Agent Registry (In-Memory)                     │   │
│  │  • Map hostname -> "ip:port"                          │   │
│  │  • Updated via /agents/register endpoint             │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files and Structure

### Core Application Files

#### `app.py` (171 lines)
Main FastAPI application entry point. Handles application initialization, middleware configuration, database setup, and the metrics ingestion endpoint.

**Key Components**:
- FastAPI app initialization
- CORS middleware configuration
- Startup event handler
- Authentication dependency
- Metrics endpoint

#### `api_routes.py` (643 lines)
Contains all API route handlers organized by functionality.

**Route Groups**:
- Host management (`/hosts/*`)
- Agent management (`/agents/*`)
- Alert management (`/alerts/*`)
- Threshold configuration (`/thresholds/*`)
- Historical metrics (`/hosts/{host_id}/metrics/historical/*`)
- Process list proxy (`/hosts/{hostname}/processes`)

#### `models.py` (64 lines)
SQLAlchemy ORM models for database tables.

**Models**:
- `Metric`: Stores time-series metrics
- `Process`: Stores process snapshots (for future use)
- `ThresholdConfig`: Stores threshold configurations
- `Alert`: Stores alert events

#### `database.py` (22 lines)
Database connection and session management.

**Components**:
- Async SQLAlchemy engine
- Async session maker
- Dependency injection function

#### `pydantic_models.py` (102 lines)
Pydantic models for request/response validation.

**Models**:
- Input models: `MetricPayload`, `AlertPayload`, `ThresholdConfigPayload`
- Response models: `AlertResponse`, `AlertListResponse`, `AlertStatsResponse`
- Nested models: `LoadAverage`, `DiskInfo`, `MemoryInfo`, `NetworkIO`

### Supporting Modules

#### `agent_registry.py` (6 lines)
In-memory registry mapping hostnames to agent addresses.

#### `discord_notifier.py` (284 lines)
Discord bot integration for sending alert notifications.

**Features**:
- Background bot initialization
- Rich embed formatting
- Alert and resolution notifications
- Thread-safe event loop integration

### Configuration

#### `requirements.txt` (26 lines)
Python package dependencies with pinned versions.

---

## Dependencies

### Core Framework Dependencies

#### FastAPI (0.119.0)
**Purpose**: High-performance web framework for building APIs

**Key Features Used**:
- Automatic OpenAPI/Swagger documentation
- Pydantic integration for request/response validation
- Async/await support
- Dependency injection system
- Route decorators
- Middleware support (CORS)

**Why FastAPI**: Provides excellent performance (comparable to Node.js), automatic API documentation, and strong type safety through Pydantic integration.

#### Uvicorn (0.37.0)
**Purpose**: ASGI server for running FastAPI applications

**Features**:
- Async server implementation
- Hot reload support (development)
- Production-ready with multiple worker support

#### Starlette (0.48.0)
**Purpose**: FastAPI's underlying framework

**Features**:
- ASGI-compatible
- Lightweight and performant
- Built-in CORS middleware

### Database Dependencies

#### SQLAlchemy (2.0.44)
**Purpose**: Python ORM and database toolkit

**Features Used**:
- Async engine (`create_async_engine`)
- Async session management (`async_sessionmaker`)
- ORM models (`declarative_base`)
- Text-based raw queries for complex SQL

#### asyncpg (0.30.0)
**Purpose**: High-performance async PostgreSQL driver

**Why**: Native async support provides better performance than synchronous drivers

**Features**:
- Full async/await support
- Connection pooling
- Prepared statement cache
- Binary protocol for efficiency

#### psycopg2-binary (2.9.11)
**Purpose**: PostgreSQL database adapter

**Note**: While asyncpg is preferred, psycopg2-binary is included for compatibility

#### TimescaleDB
**Purpose**: PostgreSQL extension for time-series data

**Features Used**:
- Hypertables for automatic partitioning
- `time_bucket()` function for aggregation
- Optimized indexes for time-series queries

**Note**: TimescaleDB must be installed as a PostgreSQL extension. The server creates hypertables automatically.

### Validation and Serialization

#### Pydantic (2.12.2)
**Purpose**: Data validation using Python type annotations

**Features Used**:
- Automatic request validation
- Type coercion
- Field aliases for JSON compatibility
- Optional/required field handling

#### pydantic-core (2.41.4)
**Purpose**: Core validation engine for Pydantic 2.x

### Integration Dependencies

#### discord.py (2.4.0)
**Purpose**: Discord bot framework

**Features Used**:
- Bot client initialization
- Channel sending
- Rich embeds
- Intents configuration

#### requests (2.32.5)
**Purpose**: HTTP client for proxying agent requests

**Features Used**:
- GET requests to agent Flask servers
- Timeout handling
- Error handling

### Configuration Dependencies

#### python-dotenv (1.1.1)
**Purpose**: Load environment variables from `.env` files

**Usage**: `load_dotenv()` at application startup

#### PyYAML (6.0.3)
**Purpose**: YAML parsing (used by dependency libraries)

---

## Core Components

### 1. Application Initialization (`app.py`)

#### FastAPI App Setup (Lines 27-39)

```python
app = FastAPI(
    title="SysSight Server",
    description="The central server for collecting and managing host metrics."
)
```

Creates the FastAPI application instance with metadata for OpenAPI documentation.

#### CORS Middleware (Lines 33-39)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Purpose**: Enable cross-origin requests from the frontend

**Configuration**:
- `allow_origins`: Frontend dev server URLs (Vite default port 5173)
- `allow_credentials`: Allow cookies/credentials
- `allow_methods`: All HTTP methods
- `allow_headers`: All headers

**Production Note**: Should be restricted to frontend production domain

#### Startup Event (Lines 44-131)

Runs once when the server starts up.

**Responsibilities**:
1. Create database tables (if not exists)
2. Ensure database schema compatibility
3. Convert metrics table to TimescaleDB hypertable
4. Initialize default threshold configurations
5. Start Discord bot in background

**Database Initialization**:
```python
async with engine.begin() as conn:
    # Create tables
    await conn.run_sync(models.Base.metadata.create_all)
    
    # Add ip_address column if missing
    await conn.execute(text("ALTER TABLE public.metrics ADD COLUMN IF NOT EXISTS ip_address VARCHAR;"))
    
    # Fix primary key for TimescaleDB compatibility
    # TimescaleDB requires timestamp in PK
    await conn.execute(text("""..."""))
    
    # Convert to hypertable
    await conn.execute(text("SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);"))
```

**Primary Key Adjustment**:
TimescaleDB requires that the primary key includes the partitioning column (timestamp). The startup logic checks if the current PK includes `timestamp`; if not, it drops and recreates with a composite key `(timestamp, id)`.

**Hypertable Creation**:
```sql
SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);
```

This converts the `metrics` table into a TimescaleDB hypertable, enabling:
- Automatic partitioning by time
- Optimized time-series queries
- Continuous aggregates
- Automatic data retention policies

**Default Thresholds**:
If no global thresholds exist, the server initializes:
- CPU > 80% (warning)
- CPU > 95% (critical)
- Memory > 85% (warning)
- Memory > 95% (critical)
- Disk > 90% (warning)

**Discord Bot Initialization**:
```python
discord_notifier.start_discord_bot()
```

Starts Discord bot in a daemon thread for background operation.

#### Authentication Dependency (Lines 133-137)

```python
async def verify_token(authorization: str = Header(...)):
    expected_token = os.getenv("SYSSIGHT_AUTH_TOKEN", "your_secret_auth_token")
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")
```

**Purpose**: Validate Bearer token for protected endpoints

**Usage**: Applied via `Depends(verify_token)` on routes requiring authentication

**Security**: Simple token comparison. In production, use JWT or OAuth2.

#### Metrics Endpoint (Lines 140-167)

```python
@app.post("/metrics", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
async def receive_and_save_metrics(payload: MetricPayload, db: AsyncSession = Depends(get_db)):
```

**Purpose**: Primary endpoint for agent metric ingestion

**Flow**:
1. Validate payload via Pydantic (`MetricPayload`)
2. Create SQLAlchemy model from payload
3. Insert into database
4. Commit transaction
5. Refresh to get generated ID
6. Return success response

**Payload Structure**:
```python
{
    "hostname": str,
    "timestamp": datetime (ISO 8601),
    "cpu_percent": float,
    "memory": {
        "total_gb": float,
        "available_gb": float,
        "percent_used": float
    },
    "disk": {
        "total_gb": float,
        "used_gb": float,
        "free_gb": float,
        "percent_used": float
    },
    "network": {
        "bytes_sent": int,
        "bytes_received": int
    },
    "load_average": {
        "1m": float,
        "5m": float,
        "15m": float
    },
    "ip_address": str (optional)
}
```

**Validation**: Pydantic automatically validates types, required fields, and data formats.

**Database Model Mapping**:
- Flattens nested structure for database storage
- Extracts `mem_percent_used` from `memory.percent_used`
- Extracts `disk_percent_used` from `disk.percent_used`
- Stores network bytes directly
- Stores individual load averages

**Response**:
```python
{
    "status": "success",
    "message": "Metric ID {id} saved"
}
```

---

### 2. Database Layer

#### Engine Configuration (`database.py`)

```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/postgres")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

**Database URL Format**:
```
postgresql+asyncpg://user:password@host:port/database
```

**Components**:
- `create_async_engine`: Creates async SQLAlchemy engine
- `async_sessionmaker`: Factory for async database sessions
- `expire_on_commit=False`: Keep objects available after commit
- `declarative_base()`: Base class for ORM models

#### Session Dependency

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**Purpose**: Dependency injection for database sessions

**Usage**: Injected into route handlers via `Depends(get_db)`

**Lifetime**: Session created per request, yielded to handler, closed after request

**Benefits**:
- Automatic connection management
- Transaction lifecycle management
- Clean resource cleanup

#### Data Models (`models.py`)

##### Metric Model

```python
class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True, index=True)
    hostname = Column(String, index=True)
    ip_address = Column(String, nullable=True)
    
    cpu_percent = Column(Float)
    mem_percent_used = Column(Float)
    disk_percent_used = Column(Float)
    net_bytes_sent = Column(BigInteger)
    net_bytes_received = Column(BigInteger)
    load_1m = Column(Float)
    load_5m = Column(Float)
    load_15m = Column(Float)
```

**Primary Key**: Composite `(timestamp, id)` - required by TimescaleDB

**Indexes**: Created on `timestamp`, `hostname`, and `id` for query performance

**Data Types**:
- `Float`: CPU, memory, disk, load (decimal values)
- `BigInteger`: Network bytes (can exceed `Integer` max)
- `DateTime(timezone=True)`: Timezone-aware timestamps
- `String`: Hostname, IP address (variable length text)

##### Alert Model

```python
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String, index=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    threshold_value = Column(Float)
    severity = Column(String)
    status = Column(String, default='active')
    message = Column(Text)
    triggered_at = Column(DateTime(timezone=True), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)
```

**Status States**: `active`, `resolved`, `acknowledged`

**Severity Levels**: `info`, `warning`, `critical`

**Lifecycle**:
1. Created with `status='active'`
2. Updated when duplicate threshold violations occur
3. Resolved via `/alerts/{id}/resolve` endpoint

**Indexes**: On `hostname`, `metric_name`, and `triggered_at` for filtering queries

##### ThresholdConfig Model

```python
class ThresholdConfig(Base):
    __tablename__ = "threshold_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String, index=True, nullable=True)  # null = global default
    metric_name = Column(String)
    operator = Column(String)
    threshold_value = Column(Float)
    severity = Column(String)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
```

**Scope**: 
- `hostname=NULL`: Global threshold (applies to all hosts)
- `hostname='specific-host'`: Host-specific threshold (overrides global)

**Enable/Disable**: `enabled=True/False` allows temporary disabling without deletion

**Audit Trail**: `created_at` and `updated_at` track configuration changes

##### Process Model (Unused)

```python
class Process(Base):
    __tablename__ = "processes"
    # ... fields for storing process snapshots
```

**Purpose**: Reserved for future feature to store process snapshots

**Note**: Currently, process data is fetched on-demand from agents

---

### 3. API Routes (`api_routes.py`)

#### Router Setup

```python
router = APIRouter()
app.include_router(router, prefix="/api/v1")
```

All routes are prefixed with `/api/v1` for versioning.

#### Allowed Metrics Whitelist

```python
ALLOWED_METRIC_TYPES = {
    "cpu_percent",
    "mem_percent_used",
    "disk_percent_used",
    "net_bytes_sent",
    "net_bytes_received",
    "load_1m",
    "load_5m",
    "load_15m"
}
```

**Purpose**: Prevent SQL injection in historical metrics queries

**Usage**: Validates metric types before building SQL queries

---

#### Host Management Endpoints

##### List Hosts (`GET /api/v1/hosts`)

```python
@router.get("/hosts")
async def list_hosts(db: AsyncSession = Depends(get_db)):
```

**Purpose**: Get all monitored hosts with their status

**Returns**:
```python
[
    {
        "host_id": "hostname",
        "hostname": "hostname",
        "ip_address": "192.168.1.100",
        "last_seen": "2024-01-01T12:00:00Z",
        "status": "online" | "offline"
    }
]
```

**Status Logic**:
- `online`: Last metric received within 5 minutes
- `offline`: Last metric older than 5 minutes

**SQL Query**:
```sql
WITH latest_metrics AS (
    SELECT DISTINCT ON (hostname) 
        hostname, ip_address, timestamp as last_seen,
        CASE 
            WHEN (NOW() - timestamp) < INTERVAL '5 minutes' THEN 'online'
            ELSE 'offline'
        END as status
    FROM metrics 
    ORDER BY hostname, timestamp DESC
)
SELECT hostname as host_id, hostname, COALESCE(ip_address, 'unknown') as ip_address,
       last_seen, status
FROM latest_metrics
ORDER BY hostname
```

**Features**:
- `DISTINCT ON (hostname)`: Gets most recent metric per host
- `COALESCE`: Uses 'unknown' if IP is NULL
- `CASE`: Calculates online/offline status

##### Get Latest Metrics (`GET /api/v1/hosts/{host_id}/metrics/latest`)

```python
@router.get("/hosts/{host_id}/metrics/latest")
async def get_latest_metrics(host_id: str, db: AsyncSession = Depends(get_db)):
```

**Purpose**: Get the most recent metrics for a host

**Returns**:
```python
{
    "host_id": "hostname",
    "timestamp": "2024-01-01T12:00:00Z",
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_usage": {"/": {"percent": 78.5}},
    "network": {"bytes_sent": 1234567, "bytes_recv": 9876543},
    "load_average": [1.23, 2.45, 3.67]
}
```

**Query**:
```sql
SELECT hostname, timestamp, cpu_percent, mem_percent_used, disk_percent_used,
       net_bytes_sent, net_bytes_received, load_1m, load_5m, load_15m
FROM metrics 
WHERE hostname = :hostname 
ORDER BY timestamp DESC 
LIMIT 1
```

**Error Handling**: 404 if host not found

##### Get Historical Metrics (`GET /api/v1/hosts/{host_id}/metrics/historical/{metric_type}`)

```python
@router.get("/hosts/{host_id}/metrics/historical/{metric_type}")
async def get_historical_metrics(
    host_id: str,
    metric_type: str,
    start_time: str = Query(...),
    end_time: str = Query(...),
    step: str = Query("1m"),
    db: AsyncSession = Depends(get_db)
):
```

**Purpose**: Get time-series data with aggregation

**Parameters**:
- `start_time`, `end_time`: ISO 8601 timestamps
- `step`: Aggregation interval (`1m`, `5m`, `1h`, `1d`)
- `metric_type`: Must be in `ALLOWED_METRIC_TYPES`

**Returns**:
```python
{
    "metric_type": "cpu_percent",
    "values": [
        [1704067200, 45.2],  # [timestamp, value]
        [1704067260, 46.1],
        ...
    ]
}
```

**Aggregation**:
Uses TimescaleDB's `time_bucket()` for efficient aggregation:
```sql
SELECT 
    EXTRACT(EPOCH FROM time_bucket(:interval, timestamp)) AS bucket_timestamp,
    AVG(cpu_percent) AS avg_value
FROM metrics 
WHERE hostname = :hostname 
  AND timestamp >= :start_time 
  AND timestamp <= :end_time
  AND cpu_percent IS NOT NULL
GROUP BY time_bucket(:interval, timestamp)
ORDER BY bucket_timestamp
```

**Step Mapping**:
```python
{
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1)
}
```

**Features**:
- Prevents NULL values from being included
- Converts timestamps to Unix epoch integers
- Rounds values to 2 decimal places
- Filters out NULL values in aggregation

---

#### Agent Registry Endpoints

##### Register Agent (`POST /api/v1/agents/register`)

```python
@router.post("/agents/register")
async def register_agent(registration_data: dict):
```

**Purpose**: Register agent's IP and port

**Payload**:
```python
{
    "hostname": "server-01",
    "ip_address": "192.168.1.100",
    "port": 9090
}
```

**Storage**: In-memory dictionary `agent_registry[hostname] = "ip:port"`

**Why**: Agents self-register their connection details for process proxying

**Returns**:
```python
{
    "status": "success",
    "message": "Agent {hostname} registered at {ip}:{port}"
}
```

**Note**: Registry is in-memory and lost on server restart. Agents re-register every 5 minutes.

##### List Agents (`GET /api/v1/agents`)

```python
@router.get("/agents")
async def list_agents():
```

**Returns**:
```python
{
    "agents": {
        "server-01": "192.168.1.100:9090",
        "server-02": "192.168.1.101:9090"
    },
    "count": 2
}
```

---

#### Process Proxy Endpoint

##### Get Host Processes (`GET /api/v1/hosts/{hostname}/processes`)

```python
@router.get("/hosts/{hostname}/processes")
async def get_host_processes(
    hostname: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("cpu_percent"),
    sort_order: str = Query("desc")
):
```

**Purpose**: Proxy process list requests to agents

**Flow**:
1. Look up agent in registry
2. Build agent URL: `http://{ip}:{port}/processes`
3. GET request to agent (10 second timeout)
4. Parse JSON response
5. Sort and paginate server-side
6. Return paginated result

**Validation**:
- `sort_by`: Must be in `{"cpu_percent", "memory_percent", "pid", "name"}`
- `sort_order`: Must be `"asc"` or `"desc"`
- `limit`: Between 1 and 100
- `page`: Must be >= 1

**Error Handling**:
- 404: Agent not in registry
- 503: Agent connection failed
- 500: Invalid agent response

**Returns**:
```python
{
    "processes": [...],  # Sorted and paginated
    "total": 150,
    "page": 1,
    "limit": 10,
    "total_pages": 15
}
```

**Architecture**: Server proxies to agent Flask servers to avoid storing process data in database

---

#### Alert Management Endpoints

##### Create Alert (`POST /api/v1/alerts`)

```python
@router.post("/alerts")
async def create_alert(alert: AlertPayload, db: AsyncSession = Depends(get_db)):
```

**Purpose**: Create or update alert

**Deduplication Logic**:
1. Check for existing active alert with same `hostname` and `metric_name`
2. If exists: Update `triggered_at` timestamp (renewal)
3. If not exists: Create new alert and send Discord notification

**Prevents**: Duplicate alerts for ongoing violations

**Flow**:
```python
existing_alert = await db.execute(
    select(models.Alert).where(
        and_(
            models.Alert.hostname == alert.hostname,
            models.Alert.metric_name == alert.metric_name,
            models.Alert.status == 'active'
        )
    )
)
```

**Discord Notification**: Sent only for new alerts, not renewals

##### List Alerts (`GET /api/v1/alerts`)

```python
@router.get("/alerts")
async def list_alerts(
    hostname: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
```

**Purpose**: List alerts with filtering and pagination

**Filters**:
- `hostname`: Filter by specific host
- `status`: Filter by `active`, `resolved`, `acknowledged`
- `severity`: Filter by `info`, `warning`, `critical`

**Pagination**:
- Default 50 per page, max 100
- Returns total count and total pages

**Ordering**: By `triggered_at` descending (newest first)

**SQL**:
```python
query = select(models.Alert)

# Apply filters
if hostname:
    query = query.where(models.Alert.hostname == hostname)
if status:
    query = query.where(models.Alert.status == status)
if severity:
    query = query.where(models.Alert.severity == severity)

# Count total
count_query = select(func.count()).select_from(query.subquery())
total = (await db.execute(count_query)).scalar()

# Paginate
query = query.order_by(desc(models.Alert.triggered_at))
query = query.offset((page - 1) * limit).limit(limit)
```

**Returns**:
```python
{
    "alerts": [...],
    "total": 145,
    "page": 1,
    "limit": 50,
    "total_pages": 3
}
```

##### Resolve Alert (`PATCH /api/v1/alerts/{alert_id}/resolve`)

```python
@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
```

**Purpose**: Mark alert as resolved

**Flow**:
1. Fetch alert by ID
2. Check if already resolved (400 if so)
3. Update status to `resolved`
4. Set `resolved_at` to current timestamp
5. Set `resolved_by` to `'system'` (in production, use actual user)
6. Send Discord resolution notification

**Discord Notification**: Includes duration (resolved_at - triggered_at)

**Returns**:
```python
{
    "status": "success",
    "message": "Alert 123 resolved"
}
```

##### Alert Stats (`GET /api/v1/alerts/stats`)

```python
@router.get("/alerts/stats")
async def get_alert_stats(db: AsyncSession = Depends(get_db)):
```

**Purpose**: Get summary statistics

**Returns**:
```python
{
    "active_count": 5,
    "resolved_count": 140,
    "by_severity": {
        "info": 0,
        "warning": 3,
        "critical": 2
    }
}
```

**Queries**:
```sql
-- Active count
SELECT COUNT(*) FROM alerts WHERE status = 'active'

-- Resolved count
SELECT COUNT(*) FROM alerts WHERE status = 'resolved'

-- By severity
SELECT severity, COUNT(*) FROM alerts 
WHERE status = 'active' 
GROUP BY severity
```

---

#### Threshold Configuration Endpoints

##### Get Thresholds (`GET /api/v1/thresholds`)

```python
@router.get("/thresholds", response_model=ThresholdConfigResponse)
async def get_thresholds(db: AsyncSession = Depends(get_db)):
```

**Purpose**: Get all global threshold configurations

**Default Fallback**: If database is empty, returns hardcoded defaults

**Returns**:
```python
{
    "thresholds": [
        {
            "id": 1,
            "metric_name": "cpu_percent",
            "operator": ">",
            "threshold_value": 80.0,
            "severity": "warning",
            "enabled": True
        },
        ...
    ]
}
```

**Query**:
```python
result = await db.execute(
    select(models.ThresholdConfig)
    .where(models.ThresholdConfig.hostname.is_(None))  # Global only
    .order_by(models.ThresholdConfig.id)
)
```

##### Update Thresholds (`PUT /api/v1/thresholds`)

```python
@router.put("/thresholds", response_model=ThresholdConfigResponse)
async def update_thresholds(
    update: ThresholdConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
```

**Purpose**: Replace all global thresholds

**Flow**:
1. Delete all global thresholds (`hostname IS NULL`)
2. Insert new thresholds from payload
3. Commit transaction
4. Refresh objects to get IDs
5. Return updated list

**Atomicity**: Transaction ensures all-or-nothing update

**Payload**:
```python
{
    "thresholds": [
        {
            "metric_name": "cpu_percent",
            "operator": ">",
            "threshold_value": 85.0,
            "severity": "warning",
            "enabled": True
        },
        ...
    ]
}
```

**SQL**:
```python
# Delete old
await db.execute(text("DELETE FROM threshold_configs WHERE hostname IS NULL"))

# Insert new
for threshold in update.thresholds:
    new_threshold = models.ThresholdConfig(
        hostname=None,
        metric_name=threshold.metric_name,
        operator=threshold.operator,
        threshold_value=threshold.threshold_value,
        severity=threshold.severity,
        enabled=threshold.enabled,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_threshold)
```

##### Reset Thresholds (`POST /api/v1/thresholds/reset`)

```python
@router.post("/thresholds/reset", response_model=ThresholdConfigResponse)
async def reset_thresholds(db: AsyncSession = Depends(get_db)):
```

**Purpose**: Reset to hardcoded default thresholds

**Flow**: Same as update, but uses `DEFAULT_THRESHOLDS` constant

---

### 4. Discord Integration (`discord_notifier.py`)

#### Architecture

**Threading**: Discord bot runs in a daemon thread to avoid blocking the main application

**Event Loop**: Separate asyncio event loop for the bot

**Initialization**:
```python
def start_discord_bot():
    def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_init_bot())
    
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
```

**Why Daemon Thread**: Terminates when main application exits

#### Bot Configuration

**Environment Variables**:
- `DISCORD_BOT_TOKEN`: Discord bot token
- `DISCORD_CHANNEL_ID`: Target channel ID

**Intents**:
```python
intents = discord.Intents.default()
intents.message_content = False  # Not needed
intents.guilds = True  # Required to see channels
```

**Why No Message Content**: Bot only sends messages, doesn't read them

#### Bot Initialization

**Startup Sequence**:
1. Check environment variables
2. Create Discord client
3. Define `on_ready` event handler
4. List available channels (for debugging)
5. Verify access to target channel
6. Start bot

**Channel Verification**:
```python
channel = _bot_client.get_channel(_channel_id)
if channel:
    print(f"✅ Discord target channel found: {channel.name}")
else:
    print("⚠️  Warning: Could not find channel {_channel_id}")
```

#### Alert Notification Function

```python
def send_alert_notification(
    alert_id: int,
    hostname: str,
    metric_name: str,
    metric_value: float,
    threshold_value: float,
    severity: str,
    message: str,
    triggered_at: datetime
) -> bool:
```

**Purpose**: Send formatted alert notification to Discord

**Embed Structure**:
```python
embed = discord.Embed(
    title=f"🚨 Alert Triggered: {severity.upper()}",
    description=message,
    color=get_severity_color(severity),
    timestamp=triggered_at
)

embed.add_field(name="🖥️ Hostname", value=hostname, inline=True)
embed.add_field(name="📊 Metric", value=metric_name, inline=True)
embed.add_field(name="📈 Current Value", value=f"{metric_value:.2f}", inline=True)
embed.add_field(name="⚠️ Threshold", value=f"{threshold_value:.2f}", inline=True)
embed.add_field(name="🔴 Severity", value=severity.upper(), inline=True)
embed.add_field(name="🕒 Triggered At", value=timestamp_str, inline=True)
```

**Color Mapping**:
- `critical`: Red (0xFF0000)
- `warning`: Orange (0xFFA500)
- `info`: Blue (0x0000FF)

**Execution**: Schedules coroutine in bot's event loop using `asyncio.run_coroutine_threadsafe()`

**Why Thread-Safe**: FastAPI runs in a different event loop, so we must safely schedule the coroutine in the bot's loop

#### Resolution Notification Function

```python
def send_resolution_notification(
    alert_id: int,
    hostname: str,
    metric_name: str,
    severity: str,
    triggered_at: datetime,
    resolved_at: datetime,
    resolved_by: Optional[str] = None
) -> bool:
```

**Purpose**: Send notification when alert is resolved

**Additional Fields**:
- Duration calculation: `resolved_at - triggered_at`
- Resolved timestamp
- Resolver (currently "system")

**Color**: Green (0x00FF00) to indicate resolution

---

### 5. Pydantic Models (`pydantic_models.py`)

#### Request Models

##### MetricPayload

```python
class MetricPayload(BaseModel):
    hostname: str
    timestamp: datetime  # Parses ISO 8601 automatically
    cpu_percent: float
    load_average: LoadAverage
    disk: DiskInfo
    memory: MemoryInfo
    network: NetworkIO
    process_count: Optional[int] = None
    ip_address: Optional[str] = None
```

**Validation**: FastAPI automatically validates JSON structure

**Nested Models**:
- `LoadAverage`: `{m1, m5, m15}` with aliases `1m`, `5m`, `15m`
- `DiskInfo`: `{total_gb, used_gb, free_gb, percent_used}`
- `MemoryInfo`: `{total_gb, available_gb, percent_used}`
- `NetworkIO`: `{bytes_sent, bytes_received}`

**Field Aliases**: Uses `Field(..., alias='1m')` for JSON compatibility

##### AlertPayload

```python
class AlertPayload(BaseModel):
    hostname: str
    metric_name: str
    metric_value: float
    threshold_value: float
    severity: str
    message: str
    timestamp: datetime
```

**Purpose**: Validate alert creation requests

#### Response Models

##### AlertResponse

```python
class AlertResponse(BaseModel):
    id: int
    hostname: str
    metric_name: str
    metric_value: float
    threshold_value: float
    severity: str
    status: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
```

**Usage**: Serializes alert objects for API responses

##### AlertListResponse

```python
class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    limit: int
    total_pages: int
```

**Purpose**: Paginated alert list with metadata

##### AlertStatsResponse

```python
class AlertStatsResponse(BaseModel):
    active_count: int
    resolved_count: int
    by_severity: dict
```

**Purpose**: Summary statistics

##### ThresholdConfigItem

```python
class ThresholdConfigItem(BaseModel):
    id: Optional[int] = None
    metric_name: str
    operator: str
    threshold_value: float
    severity: str
    enabled: bool = True
```

**Purpose**: Individual threshold configuration

##### ThresholdConfigResponse

```python
class ThresholdConfigResponse(BaseModel):
    thresholds: List[ThresholdConfigItem]
```

**Purpose**: List of threshold configurations

##### ThresholdConfigUpdate

```python
class ThresholdConfigUpdate(BaseModel):
    thresholds: List[ThresholdConfigItem]
```

**Purpose**: Update payload for threshold endpoints

---

## Async Architecture

### Why Async?

**Benefits**:
1. **I/O Performance**: Database queries and HTTP requests don't block
2. **Concurrency**: Handle multiple requests simultaneously
3. **Scalability**: Single process can handle many concurrent requests
4. **Responsiveness**: Non-blocking I/O operations

### Async Patterns Used

#### Async Database Queries

```python
result = await db.execute(select(models.Alert))
alerts = result.scalars().all()
```

**Blocking Version** (Not Used):
```python
result = db.execute(select(models.Alert))
alerts = result.scalars().all()
```

**Difference**: `await` allows other coroutines to run during database I/O

#### Async Session Management

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**Context Manager**: Automatically manages transaction and cleanup

#### Async HTTP Requests

**Agent Process Proxy**:
```python
response = requests.get(agent_url, timeout=10)
```

**Note**: `requests` is synchronous. For true async, use `httpx` or `aiohttp`. Current implementation blocks during agent communication, but this is acceptable because it's infrequent.

#### Discord Bot Integration

**Thread Safety**:
```python
future = asyncio.run_coroutine_threadsafe(_send_embed(embed), loop)
result = future.result(timeout=10)
```

**Why**: FastAPI's event loop is different from Discord bot's event loop. `run_coroutine_threadsafe` schedules coroutines across event loops safely.

### Async Execution Flow

```
Request arrives at FastAPI
    ↓
Route handler starts (async function)
    ↓
Database query executes (await)
    │
    ├─→ Other requests can be processed
    │
    ↓
Database returns result
    ↓
Transform data
    ↓
Return JSON response
```

**Key Point**: During database I/O, the event loop can process other requests, maximizing throughput.

---

## Data Flow

### Metric Ingestion Flow

```
Agent sends POST /metrics
    ↓
FastAPI receives request
    ↓
verify_token dependency checks auth
    ↓
Pydantic validates MetricPayload
    ↓
Route handler creates Metric model
    ↓
Session.add(new_metric)
    ↓
await db.commit()  # Flush to database
    ↓
await db.refresh(new_metric)  # Get generated ID
    ↓
Return success response
```

### Alert Creation Flow

```
Agent evaluates threshold violation
    ↓
Agent sends POST /api/v1/alerts
    ↓
Server validates AlertPayload
    ↓
Check for existing active alert
    ├─→ Exists: Update triggered_at (renewal)
    └─→ Not exists: Create new alert
         ↓
         Insert into database
         ↓
         await db.commit()
         ↓
         Send Discord notification (async)
         ↓
         Return alert ID
```

### Historical Metrics Query Flow

```
Frontend requests GET /api/v1/hosts/{id}/metrics/historical/cpu_percent
    ↓
Validate metric_type (SQL injection prevention)
    ↓
Parse start_time and end_time
    ↓
Map step string to timedelta
    ↓
Build TimescaleDB query with time_bucket
    ↓
Execute query (async)
    │
    ├─→ TimescaleDB aggregates data
    │
    ↓
Transform results to [[timestamp, value], ...]
    ↓
Return JSON response
```

### Process Proxy Flow

```
Frontend requests GET /api/v1/hosts/{hostname}/processes
    ↓
Look up agent in registry
    ├─→ Not found: 404 error
    └─→ Found: Continue
         ↓
         Build agent URL: http://{ip}:{port}/processes
         ↓
         requests.get(agent_url, timeout=10)
         │
         ├─→ Error: 503 Service Unavailable
         └─→ Success: Continue
              ↓
              Parse JSON response
              ↓
              Sort by sort_by parameter
              ↓
              Paginate results
              ↓
              Return paginated JSON
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/postgres` | PostgreSQL connection string |
| `SYSSIGHT_AUTH_TOKEN` | `your_secret_auth_token` | Bearer token for authentication |
| `DISCORD_BOT_TOKEN` | *None* | Discord bot token (optional) |
| `DISCORD_CHANNEL_ID` | *None* | Discord channel ID (optional) |

### Database Setup

**Prerequisites**:
1. PostgreSQL installed
2. TimescaleDB extension installed

**Create Database**:
```bash
createdb syssight
```

**Enable TimescaleDB**:
```bash
psql syssight -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

**Connection String Format**:
```
postgresql+asyncpg://user:password@host:port/database
```

### Authentication

**Bearer Token Format**:
```
Authorization: Bearer your_secret_auth_token
```

**Securing in Production**:
- Use strong, randomly generated tokens
- Store tokens securely (environment variables, secrets management)
- Rotate tokens periodically
- Consider JWT for user-based auth

---

## Error Handling

### Global Error Handling

FastAPI's default exception handlers return JSON error responses:

**404 Not Found**:
```json
{
  "detail": "Host not found"
}
```

**400 Bad Request**:
```json
{
  "detail": "Invalid metric_type. Allowed: cpu_percent, mem_percent_used, ..."
}
```

**401 Unauthorized**:
```json
{
  "detail": "Invalid authorization token"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error"
}
```

### Database Error Handling

**Connection Errors**:
- SQLAlchemy pool handles reconnection automatically
- Logged but don't crash the server

**Query Errors**:
- Caught and returned as 500 errors
- Should not expose SQL details in production

### Agent Communication Errors

**Process Proxy Failures**:
- Returns 503 Service Unavailable
- Includes error message from agent connection attempt
- Frontend can retry or show "agent offline" message

### Discord Integration Errors

**Bot Not Configured**:
- Server continues operating
- Prints warning message
- Returns `False` from notification functions

**Channel Not Found**:
- Logs warning
- Does not crash the server
- Alerts still created in database

---

## Security

### Input Validation

**SQL Injection Prevention**:
1. **Whitelist metric types**: `ALLOWED_METRIC_TYPES` set
2. **Parameterized queries**: SQLAlchemy uses bind parameters
3. **Pydantic validation**: Request payloads validated by type

**Example**: Historical metrics endpoint
```python
if metric_type not in ALLOWED_METRIC_TYPES:
    raise HTTPException(status_code=400)

# Safe: column name from whitelist
query_sql = f"SELECT AVG({metric_col}) FROM ..."
```

### Authentication

**Bearer Token**: Simple token-based auth for agent endpoints

**Limitations**:
- Token stored in plain text
- No user management
- No expiration

**Production Recommendations**:
- Use JWT tokens with expiration
- Implement user authentication
- Use OAuth2 for third-party integrations

### CORS Configuration

**Current**: Allows localhost development

**Production**: Should restrict to frontend domain:
```python
allow_origins=["https://yourdomain.com"]
```

### Rate Limiting

**Not Implemented**: Vulnerable to DoS attacks

**Recommendations**:
- Add rate limiting middleware (slowapi)
- Per-IP rate limits
- Per-endpoint rate limits

---

## Best Practices

### Database Best Practices

#### Index Strategy

**Indexes Created**:
- `timestamp` (primary key component)
- `hostname` (frequent filtering)
- `id` (lookups)
- `triggered_at` on alerts (ordering)
- `metric_name` on alerts (filtering)

**Why**: Indexes speed up common query patterns

#### Query Optimization

**DISTINCT ON**:
```sql
SELECT DISTINCT ON (hostname) ...
```
More efficient than `GROUP BY` for this use case

**Aggregation**:
```sql
AVG(cpu_percent)
```
Uses built-in SQL functions for efficiency

#### Connection Pooling

SQLAlchemy automatically pools connections. Configure pool size if needed:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0
)
```

### API Design Best Practices

#### Versioning

Routes prefixed with `/api/v1` for future compatibility

#### Pagination

Consistent pagination across all list endpoints:
```python
page: int = Query(1, ge=1)
limit: int = Query(50, ge=1, le=100)
```

#### Error Responses

Consistent error format:
```json
{
  "detail": "Human-readable error message"
}
```

#### Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication failed
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Code Organization

#### Separation of Concerns

- `app.py`: Application setup and main endpoint
- `api_routes.py`: All API routes
- `models.py`: Database models
- `database.py`: Database configuration
- `pydantic_models.py`: Request/response models
- `discord_notifier.py`: Discord integration
- `agent_registry.py`: Agent registry logic

#### Modularity

Each file has a single responsibility

#### Dependency Injection

Used throughout for testability:
```python
async def my_route(db: AsyncSession = Depends(get_db)):
    ...
```

### Testing Considerations

**Async Testing**:
```python
@pytest.mark.asyncio
async def test_endpoint(client):
    response = await client.post("/metrics", json={...})
    assert response.status_code == 201
```

**Database Testing**:
- Use test database
- Clean data between tests
- Use fixtures for database setup

**Mocking**:
- Mock agent HTTP requests
- Mock Discord bot in tests

---

## Performance Optimization

### Database Optimizations

#### TimescaleDB Hypertables

Automatic partitioning by time improves query performance for time-series data

#### Indexes

Strategic indexes on frequently queried columns

#### Query Optimization

Use `LIMIT` and `OFFSET` for pagination instead of fetching all data

### Async I/O

All database operations are async, allowing concurrent request handling

### Connection Pooling

SQLAlchemy manages connection pool automatically

### Caching (Not Implemented)

Consider adding Redis for:
- Agent registry (survives restarts)
- Frequently accessed thresholds
- Rate limiting tokens

---

## Monitoring and Observability

### Logging

**Current**: Print statements

**Production**: Use structured logging:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Metric saved", extra={"hostname": hostname, "id": id})
```

### Metrics (Not Implemented)

Consider adding:
- Request duration
- Request rate
- Error rate
- Database query duration
- Active connections

### Health Check (Not Implemented)

Add endpoint:
```python
@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## Deployment

### Running the Server

**Development**:
```bash
cd server
python -m uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

**Production**:
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

Create `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/postgres
SYSSIGHT_AUTH_TOKEN=your_secret_token_here
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_channel_id
```

### Docker Deployment (Not Provided)

Consider creating Dockerfile for containerized deployment

### Reverse Proxy

Use nginx or Traefik as reverse proxy:
- SSL termination
- Load balancing
- Rate limiting

---

## Troubleshooting

### Server Won't Start

**Database Connection Issues**:
- Check `DATABASE_URL` is correct
- Verify PostgreSQL is running
- Check firewall rules
- Test connection: `psql $DATABASE_URL`

**Port Already in Use**:
- Change port: `--port 8001`
- Kill existing process: `lsof -ti:8000 | xargs kill`

### Discord Notifications Not Working

**Check Environment Variables**:
```bash
echo $DISCORD_BOT_TOKEN
echo $DISCORD_CHANNEL_ID
```

**Verify Bot Permissions**:
- Bot must be in the Discord server
- Bot must have "Send Messages" permission
- Channel ID must be correct

**Check Console Logs**:
- Look for bot connection messages
- Check for error messages

### Database Performance Issues

**Check Hypertable**:
```sql
SELECT * FROM timescaledb_information.hypertables;
```

**Analyze Queries**:
```sql
EXPLAIN ANALYZE SELECT ...;
```

**Index Usage**:
```sql
SELECT * FROM pg_stat_user_indexes;
```

### Agent Connection Issues

**Check Agent Registry**:
```bash
curl http://localhost:8000/api/v1/agents
```

**Check Agent Flask Server**:
```bash
curl http://AGENT_IP:9090/processes
```

---

## Future Enhancements

### Potential Improvements

1. **User Authentication**: JWT-based auth with user management
2. **Host-Specific Thresholds**: Per-host threshold configuration
3. **Alert Acknowledgment**: Mark alerts as acknowledged by users
4. **Alert Rules**: Complex alerting rules (AND/OR conditions)
5. **Historical Process Data**: Store process snapshots in database
6. **Webhook Support**: Generic webhook notifications beyond Discord
7. **Metrics Export**: Export metrics to Prometheus/InfluxDB
8. **Dashboard Embedding**: Embeddable dashboards
9. **Multi-Database Support**: Support for MySQL, SQLite
10. **Batch Operations**: Bulk alert resolution

### Database Improvements

1. **Data Retention**: Automatic old data deletion
2. **Continuous Aggregates**: Pre-computed aggregations
3. **Compression**: Automatic compression of old data
4. **Partitioning Strategy**: Custom partitioning intervals

### API Improvements

1. **WebSocket Support**: Real-time metric streaming
2. **GraphQL**: Alternative to REST API
3. **Bulk Endpoints**: Batch operations
4. **Export Endpoints**: CSV/JSON export of metrics

---

## Conclusion

The SysSight Server is a production-ready monitoring system built on modern Python technologies. It leverages FastAPI's async capabilities, TimescaleDB's time-series optimizations, and Discord integration for real-time alerting.

The architecture is modular, scalable, and maintainable. The server can handle multiple concurrent agents, provides efficient time-series queries, and manages alert lifecycle automatically.

Key strengths include:
- Async I/O for performance
- TimescaleDB for efficient time-series storage
- Automatic threshold configuration
- Real-time Discord notifications
- Comprehensive API for frontend integration

With proper deployment configuration (environment variables, reverse proxy, SSL), this server is suitable for production monitoring systems.
