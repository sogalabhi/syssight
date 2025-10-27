# SysSight Database Strategy

## Overview

SysSight uses a **two-tier storage approach** combining persistent and in-memory data storage for optimal performance, simplicity, and scalability.

```
┌─────────────────────────────────────────────────────────────┐
│                    Storage Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Persistent Layer (TimescaleDB)                             │
│  ├── Metrics (time-series data)                             │
│  ├── Alerts (alert history)                                 │
│  └── Configurations (thresholds)                            │
│                                                              │
│  In-Memory Layer (Python Dictionary)                       │
│  └── Agent Registry (hostname → ip:port mapping)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Persistent Storage: TimescaleDB (PostgreSQL Extension)

### What It Is

**TimescaleDB** is a PostgreSQL extension that provides time-series database capabilities. It's not a separate database—it extends PostgreSQL with specialized features for handling time-series data efficiently.

### Why We Chose TimescaleDB

#### 1. **Built for Time-Series Data**

**Problem**: Regular SQL databases struggle with time-series data at scale.

```sql
-- Regular PostgreSQL table (slower with millions of rows)
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    cpu_percent FLOAT
);

-- After 1 year with 5 hosts: 2.6 million rows
-- Query performance degrades significantly
SELECT * FROM metrics 
WHERE timestamp > '2024-01-01' 
ORDER BY timestamp DESC 
LIMIT 100;
-- Full table scan: ~500ms on 2.6M rows
```

**Solution**: TimescaleDB hypertables automatically partition data by time.

```sql
-- Convert table to hypertable (one-time operation)
SELECT create_hypertable('metrics', 'timestamp');

-- Same query now only scans relevant partitions
SELECT * FROM metrics 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC 
LIMIT 100;
-- Partition pruning: ~50ms on 2.6M rows
```

**Performance Improvement**: 10x faster queries on large datasets.

#### 2. **Automatic Time-Based Partitioning**

**How It Works**:

```
Traditional Table:
┌──────────────────────────────────────────────┐
│              metrics (2.6M rows)             │
│  [All data in single table]                  │
└──────────────────────────────────────────────┘
        Query: Scans ALL 2.6M rows ❌

TimescaleDB Hypertable:
┌─────────────┬─────────────┬─────────────┐
│ Partition   │ Partition   │ Partition   │
│ 2024-01-01  │ 2024-01-02  │ 2024-01-03  │
│ 7,200 rows  │ 7,200 rows  │ 7,200 rows  │
└─────────────┴─────────────┴─────────────┘
        Query: Scans only relevant partition ✅
```

**Benefits**:
- **Query performance**: Only scans partitions containing data in time range
- **Parallelization**: Can query multiple partitions simultaneously
- **Maintenance**: Automatic data retention policies
- **Scaling**: Add more partitions as data grows

#### 3. **SQL Compatibility**

**Why this matters**: We can use standard SQL and existing PostgreSQL tools.

```python
# SQLAlchemy works seamlessly
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Standard PostgreSQL connection string
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/postgres"

# TimescaleDB is just an extension - no special client needed
engine = create_async_engine(DATABASE_URL)
```

**Advantages**:
- Use familiar SQL syntax (not a custom query language)
- Reuse existing PostgreSQL drivers (psycopg2, asyncpg)
- Compatible with SQLAlchemy ORM (no changes to our code)
- PostgreSQL tooling works (pgAdmin, DBeaver, etc.)

#### 4. **Single Database for Multiple Use Cases**

**Our schema**:

```python
# Time-series data: metrics table (hypertable)
class Metric(Base):
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    hostname = Column(String, index=True)
    cpu_percent = Column(Float)
    # ... other metrics

# Relational data: alerts table (regular table)
class Alert(Base):
    id = Column(Integer, primary_key=True)
    hostname = Column(String, index=True)
    metric_name = Column(String, index=True)
    triggered_at = Column(DateTime(timezone=True))
    # ... can JOIN with metrics if needed

# Configuration data: threshold_configs table (regular table)
class ThresholdConfig(Base):
    id = Column(Integer, primary_key=True)
    hostname = Column(String, index=True, nullable=True)
    metric_name = Column(String)
    threshold_value = Column(Float)
    # ... configuration data
```

**Benefits**:
- **Metrics** use hypertable (time-series optimized)
- **Alerts** use regular table (relational data)
- **Configs** use regular table (configuration data)
- All in one database, can JOIN across tables if needed

#### 5. **Continuous Aggregates (Future Feature)**

**What it does**: Pre-compute aggregations for faster queries.

```sql
-- Example: Create continuous aggregate for hourly CPU averages
CREATE MATERIALIZED VIEW hourly_cpu_avg
WITH (timescaledb.continuous) AS
SELECT 
    hostname,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(cpu_percent) AS avg_cpu
FROM metrics
GROUP BY hostname, hour;

-- Query from aggregate (instant):
SELECT * FROM hourly_cpu_avg 
WHERE hour > NOW() - INTERVAL '7 days';
-- vs scanning millions of rows: 100x faster
```

**When to use**: For dashboards showing historical trends (last 30 days, averages, etc.)

#### 6. **Automatic Data Retention (Future Feature)**

**Problem**: Data grows indefinitely, disk fills up.

**Solution**: Automatic cleanup of old data.

```sql
-- Automatically delete data older than 90 days
SELECT add_retention_policy('metrics', INTERVAL '90 days');

-- Old data automatically deleted
-- Keeps database size manageable
-- Reduces backup sizes
```

### Setup Instructions

#### Option 1: Docker (Recommended)

```bash
# Run TimescaleDB container
docker run -d --name syssight-timescale \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  timescale/timescaledb:latest-pg16

# Verify it's running
docker ps | grep syssight-timescale

# Check TimescaleDB extension
docker exec -it syssight-timescale psql -U postgres -c "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';"
```

#### Option 2: Local Installation

```bash
# macOS
brew install timescaledb
brew services start timescaledb

# Ubuntu/Debian
# Follow: https://docs.timescale.com/install/latest/self-hosted/

# Windows
# Download from: https://www.timescale.com/download
```

#### Configuration

**Environment Variable**:

```bash
# Create .env file in server/ directory
echo "DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/postgres" > server/.env
```

**Database Initialization** (automatic on server startup):

```python
# server/app.py - runs on startup
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(models.Base.metadata.create_all)
        
        # Convert to hypertable (idempotent)
        await conn.execute(text(
            "SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);"
        ))
```

**Verify Setup**:

```bash
# Connect to database
docker exec -it syssight-timescale psql -U postgres

# Check hypertables
SELECT hypertable_name, num_chunks 
FROM timescaledb_information.hypertables;
```

Expected output:
```
 hypertable_name | num_chunks 
-----------------+------------
 metrics         |          X
```

### Example Usage

**Storing Metrics**:

```python
# server/app.py
@app.post("/metrics")
async def receive_and_save_metrics(payload: MetricPayload, db: AsyncSession = Depends(get_db)):
    new_metric = models.Metric(
        hostname=payload.hostname,
        timestamp=payload.timestamp,
        cpu_percent=payload.cpu_percent,
        # ... other fields
    )
    db.add(new_metric)
    await db.commit()
```

**Querying Metrics**:

```python
# server/api_routes.py
async def get_latest_metrics(db: AsyncSession = Depends(get_db)):
    # TimescaleDB automatically optimizes this query
    result = await db.execute(
        select(models.Metric)
        .where(models.Metric.hostname == hostname)
        .order_by(models.Metric.timestamp.desc())
        .limit(100)
    )
    return result.scalars().all()
```

### Why Not InfluxDB?

**InfluxDB** is another time-series database. Why we didn't choose it:

#### 1. **Custom Query Language (InfluxQL)**

```influxql
-- InfluxQL (different from SQL)
SELECT mean("cpu_percent") 
FROM "metrics" 
WHERE time > now() - 1h 
GROUP BY time(10m), "hostname"
```

**Problem**: Team needs to learn new query language, different from SQL.

**vs PostgreSQL/TimescaleDB**:

```sql
-- Standard SQL (we already know this)
SELECT AVG(cpu_percent), hostname
FROM metrics 
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY hostname, time_bucket('10 minutes', timestamp)
```

#### 2. **No SQLAlchemy Support**

**TimescaleDB**: Full SQLAlchemy ORM support

```python
# We can use SQLAlchemy
from sqlalchemy.orm import Session
result = session.query(Metric).filter(...).all()
```

**InfluxDB**: Requires separate client library

```python
# Need influxdb-python client
from influxdb import InfluxDBClient
client = InfluxDBClient(host, port, database)
result = client.query('SELECT * FROM metrics')
# Different API, less type safety
```

#### 3. **Separate System to Maintain**

**TimescaleDB**: PostgreSQL extension, single system.

**InfluxDB**: Separate database with different backup, monitoring, deployment requirements.

#### 4. **When InfluxDB Would Be Better**

InfluxDB is superior if:
- Need millions of metrics per second
- Cluster/scale horizontally from start
- Team already uses InfluxDB
- Specialized time-series functions only InfluxDB provides

**Our scale**: ~10-100 metrics per second → TimescaleDB is sufficient

### Why Not MongoDB?

**MongoDB** is a document database. Why we didn't choose it:

#### 1. **Not Optimized for Time-Series**

**Problem**: MongoDB stores documents, not time-series data.

```javascript
// MongoDB document
{
  "_id": ObjectId("..."),
  "hostname": "server-01",
  "timestamp": ISODate("2024-01-01T10:00:00Z"),
  "cpu_percent": 75.5
}
// No automatic time-based partitioning
// Queries scan all documents
```

**vs TimescaleDB**:
```sql
-- Automatic partitioning
-- Only scans relevant time partitions
```

#### 2. **No Automatic Partitioning**

MongoDB requires manual sharding configuration:

```javascript
// Manual sharding setup (complex)
sh.enableSharding("syssight")
sh.shardCollection("syssight.metrics", {hostname: 1, timestamp: 1})
// Need to plan sharding strategy upfront
```

TimescaleDB does this automatically on timestamp.

#### 3. **Less Relational**

**Our data**:

```python
# Metrics and alerts are related
class Metric:
    hostname = "server-01"
    cpu_percent = 95.0

class Alert:
    hostname = "server-01"  # Same hostname
    metric_name = "cpu_percent"
    # Relational data
```

**MongoDB**: Would need manual joins or duplicate data.

**PostgreSQL**: Native JOINs, foreign keys, integrity.

#### 4. **When MongoDB Would Be Better**

MongoDB is superior if:
- Schemaless data (no fixed structure)
- Need horizontal scaling immediately
- Document-oriented data (not time-series)
- Team already uses MongoDB

**Our data**: Has schema, is time-series → PostgreSQL/TimescaleDB better fit

---

## 2. In-Memory Storage: Python Dictionary

### What It Is

**In-Memory Dictionary** is a simple Python dict used to store agent registry (hostname → ip:port mappings).

```python
# server/agent_registry.py
agent_registry: Dict[str, str] = {}
```

### Why We Chose In-Memory Dictionary

#### 1. **Simple Data Structure**

**What we store**:

```python
agent_registry = {
    "server-01": "192.168.1.100:9090",
    "server-02": "192.168.1.101:9090",
    "server-03": "192.168.1.102:9090"
}
```

**Characteristics**:
- Simple key-value mapping
- Lookup is O(1) - instant
- No complex queries needed
- No relationships or joins

#### 2. **Volatile Data**

**Why not in database**:

```python
# Agent registry data changes frequently
- Agent restarts → registry updated
- Network IP changes → registry updated  
- Agent goes offline → registry updated
- Agent comes online → registry updated
```

**Problem with database**:
```python
# Every lookup requires database query
async def get_agent_url(hostname: str):
    result = await db.execute(
        select(Agent).where(Agent.hostname == hostname)
    )
    agent = result.scalar()
    return f"{agent.ip}:{agent.port}"
# Latency: ~5-10ms per lookup
```

**vs In-memory**:
```python
# Direct dictionary lookup
async def get_agent_url(hostname: str):
    return agent_registry.get(hostname)
# Latency: ~0.001ms (5,000x faster)
```

#### 3. **Temporary Nature**

**Agent registry is temporary**:
- Lost on server restart (agents re-register)
- Not critical data (doesn't need backup)
- Changes frequently (doesn't need persistence)
- Agent re-registration handles recovery

**Database persistence not needed**:
- Metrics: Need to persist ✅
- Alerts: Need to persist ✅
- Configs: Need to persist ✅
- Agent registry: Temporary, recreated on restart ✅

#### 4. **Performance**

**Lookup performance comparison**:

```
In-Memory Dict:    ~0.001ms  (instant)
Redis:             ~0.5ms    (network roundtrip)
PostgreSQL:        ~5-10ms   (database query)
```

**For our use case**:
- Agents query registry frequently (every request)
- Sub-millisecond latency matters
- In-memory dict provides best performance

### Setup Instructions

**No setup needed** - it's just Python code:

```python
# server/agent_registry.py
from typing import Dict

# Agent registry: maps hostname -> "ip:port"
agent_registry: Dict[str, str] = {}

# Register agent
def register_agent(hostname: str, url: str):
    agent_registry[hostname] = url

# Get agent URL
def get_agent_url(hostname: str) -> str:
    return agent_registry.get(hostname)

# List all agents
def list_agents() -> Dict[str, str]:
    return agent_registry.copy()
```

### Example Usage

**Agent Registration**:

```python
# server/api_routes.py
@router.post("/agents/register")
async def register_agent(payload: AgentRegistration, db: AsyncSession = Depends(get_db)):
    # Store in-memory registry
    agent_registry[payload.hostname] = f"{payload.ip}:{payload.port}"
    
    # Persist to database (metadata only, not connection details)
    agent = models.Agent(
        hostname=payload.hostname,
        last_seen=datetime.now()
    )
    db.add(agent)
    await db.commit()
```

**Agent Lookup**:

```python
# server/api_routes.py
@router.get("/agents/{hostname}/processes")
async def get_agent_processes(hostname: str, page: int = 1, limit: int = 50):
    # Lookup from in-memory registry (fast)
    agent_url = agent_registry.get(hostname)
    if not agent_url:
        raise HTTPException(404, "Agent not found")
    
    # Proxy request to agent
    response = requests.get(f"http://{agent_url}/processes?page={page}&limit={limit}")
    return response.json()
```

### Why Not Redis?

**Redis** is an in-memory key-value store. Why we didn't choose it:

#### 1. **External Dependency**

**Problem**: Would need Redis server running:

```bash
# Additional server to maintain
docker run -d --name syssight-redis -p 6379:6379 redis

# More complexity in deployment
```

**Current approach**: No additional server needed - just Python dict.

#### 2. **Network Latency**

**Redis**:

```python
import redis
client = redis.Redis(host='localhost', port=6379)

# Lookup requires network roundtrip
agent_url = client.get(f"agent:{hostname}")
# Latency: ~0.5ms
```

**vs In-memory dict**:

```python
# Direct memory access
agent_url = agent_registry.get(hostname)
# Latency: ~0.001ms (500x faster)
```

#### 3. **Persistence Not Needed**

**Redis advantage**: Persists data to disk.

**For our use case**: Don't need persistence - agents re-register on server restart.

**Redis disadvantage**: Additional complexity without benefit.

#### 4. **When Redis Would Be Better**

Redis would be superior if:
- Need to share state across multiple server instances
- Need Redis features (pub/sub, transactions)
- Need data persistence across restarts
- Already have Redis in infrastructure

**For single-server deployment**: In-memory dict is simpler

### Why Not PostgreSQL for Registry?

**Could store in PostgreSQL**:

```python
class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String)
    port = Column(Integer)
    last_seen = Column(DateTime)
```

**Why we don't**:

#### 1. **Query Overhead**

```python
# Database query
result = await db.execute(
    select(Agent).where(Agent.hostname == hostname)
)
agent = result.scalar()
# Latency: ~5-10ms

# vs In-memory dict
agent_url = agent_registry.get(hostname)
# Latency: ~0.001ms (5,000x faster)
```

#### 2. **Connection Overhead**

Every lookup requires:
- Database connection from pool
- SQL query execution
- Result serialization
- Connection return to pool

**For simple key-value lookups**: Overkill

#### 3. **Persistence Not Needed**

Registry data is:
- Temporary (agents re-register)
- Not critical (lost on restart OK)
- Frequently changing (not worth persisting)

**Database persistence**: Not needed for this use case

---

## Architecture Summary

### Data Types and Storage

| Data Type | Storage Layer | Reason |
|-----------|---------------|--------|
| **Metrics** | TimescaleDB hypertable | Time-series optimization, queries, retention |
| **Alerts** | PostgreSQL regular table | Relational data, joins, history |
| **Thresholds** | PostgreSQL regular table | Configuration data, updates |
| **Agent Registry** | In-memory dict | Temporary, fast lookups, volatile |

### Query Patterns

**Time-series queries** (use hypertable):
```sql
-- Get latest 100 metrics
SELECT * FROM metrics 
WHERE hostname = 'server-01' 
ORDER BY timestamp DESC 
LIMIT 100;
```

**Relational queries** (use regular tables):
```sql
-- Join alerts with threshold configs
SELECT a.hostname, a.severity, t.threshold_value
FROM alerts a
JOIN threshold_configs t ON t.metric_name = a.metric_name;
```

**Fast lookups** (use in-memory):
```python
# Agent URL lookup
agent_url = agent_registry.get(hostname)  # ~0.001ms
```

### Performance Characteristics

**TimescaleDB**:
- Insert: ~1ms per metric
- Query last hour: ~50ms
- Query last day: ~200ms
- Handles millions of rows efficiently

**In-Memory Dict**:
- Lookup: ~0.001ms
- Update: ~0.001ms
- No persistence overhead

**Combined**: Best of both worlds ✅

---

## Future Enhancements

### 1. **Continuous Aggregates**

**Add pre-computed aggregations** for dashboard performance:

```sql
-- Create aggregate view
CREATE MATERIALIZED VIEW hourly_metrics AS
SELECT 
    hostname,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(cpu_percent) AS avg_cpu,
    AVG(mem_percent_used) AS avg_mem
FROM metrics
GROUP BY hostname, hour;

-- Dashboard queries aggregate view (much faster)
```

### 2. **Data Retention Policies**

**Automatically delete old data**:

```sql
-- Keep only last 90 days
SELECT add_retention_policy('metrics', INTERVAL '90 days');

-- Optional: downsample first
SELECT add_retention_policy('hourly_metrics', INTERVAL '365 days');
```

### 3. **Caching Layer (If Needed)**

**Add Redis if scaling**:
- Multiple server instances
- High-frequency queries
- Need to share state across instances

**For current scale**: Not needed

### 4. **Read Replicas (If Scaling)**

**For high read load**:
- Master database for writes
- Read replicas for dashboard queries
- Load balancer distributes read traffic

**For current scale**: Single instance sufficient

---

## Conclusion

SysSight uses a **hybrid storage approach**:

1. **TimescaleDB** (PostgreSQL extension) for persistent time-series data
   - Fast queries on large datasets
   - Automatic partitioning
   - SQL compatibility
   - Single database for all data types

2. **In-memory dict** for temporary, fast lookups
   - Minimal latency
   - Simple to use
   - No overhead

**Key Principle**: Use the right storage for each use case
- Persistent data → Database
- Temporary data → In-memory
- Time-series → TimescaleDB
- Fast lookups → Dict

This approach provides:
- ✅ Excellent performance
- ✅ Simple deployment
- ✅ Easy to maintain
- ✅ Scales to hundreds of agents
- ✅ Can be enhanced (continuous aggregates, retention policies)

---

## References

- **TimescaleDB Documentation**: https://docs.timescale.com/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Agent Registry Code**: `server/agent_registry.py`
- **Database Models**: `server/models.py`
- **Database Setup**: `server/database.py`
