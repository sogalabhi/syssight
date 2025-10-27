# SysSight SQL Queries Reference

This document lists all SQL queries used in the SysSight project, organized by category and purpose.

## Table of Contents
1. [Database Initialization](#database-initialization)
2. [Host Queries](#host-queries)
3. [Metric Queries](#metric-queries)
4. [Alert Queries](#alert-queries)
5. [Threshold Configuration Queries](#threshold-configuration-queries)
6. [Query Patterns with SQLAlchemy](#query-patterns-with-sqlalchemy)

---

## Database Initialization

### 1. Add Column: `ip_address`
**File**: `server/app.py` (line 53)

```sql
ALTER TABLE public.metrics ADD COLUMN IF NOT EXISTS ip_address VARCHAR;
```

**Purpose**: Adds the `ip_address` column to the metrics table if it doesn't exist.

**When**: Runs on server startup (idempotent).

---

### 2. Fix Primary Key for TimescaleDB
**File**: `server/app.py` (lines 56-87)

```sql
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'metrics'
          AND constraint_type = 'PRIMARY KEY'
    ) THEN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.key_column_usage
            WHERE table_schema = 'public'
              AND table_name = 'metrics'
              AND constraint_name = (
                  SELECT constraint_name FROM information_schema.table_constraints
                  WHERE table_schema = 'public' AND table_name = 'metrics' AND constraint_type = 'PRIMARY KEY'
              )
              AND column_name = 'timestamp'
        ) THEN
            EXECUTE 'ALTER TABLE public.metrics DROP CONSTRAINT ' || (
                SELECT constraint_name FROM information_schema.table_constraints
                WHERE table_schema = 'public' AND table_name = 'metrics' AND constraint_type = 'PRIMARY KEY'
            );
            EXECUTE 'ALTER TABLE public.metrics ADD PRIMARY KEY (timestamp, id)';
        END IF;
    ELSE
        EXECUTE 'ALTER TABLE public.metrics ADD PRIMARY KEY (timestamp, id)';
    END IF;
END$$;
```

**Purpose**: Ensures the primary key includes `timestamp` (required by TimescaleDB for hypertables).

**Why**: TimescaleDB hypertables require the partitioning key (timestamp) to be included in the primary key for proper chunk management.

**When**: Runs on server startup (idempotent).

---

### 3. Create Hypertable
**File**: `server/app.py` (line 90)

```sql
SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);
```

**Purpose**: Converts the `metrics` table into a TimescaleDB hypertable.

**Parameters**:
- `'metrics'`: Table name
- `'timestamp'`: Partitioning column
- `if_not_exists => TRUE`: Prevents errors on re-runs

**Why**: Enables automatic time-based partitioning for efficient time-series queries.

**When**: Runs on server startup (idempotent).

---

### 4. Check if Thresholds Exist
**File**: `server/app.py` (line 96)

```sql
SELECT COUNT(*) FROM threshold_configs WHERE hostname IS NULL;
```

**Purpose**: Checks if global default thresholds have been initialized.

**Result**: Returns count of existing global thresholds (0 if none exist).

**When**: Runs on server startup to determine if default thresholds need to be created.

---

### 5. Initialize Default Thresholds
**File**: `server/app.py` (lines 113-116)

```sql
INSERT INTO threshold_configs 
(hostname, metric_name, operator, threshold_value, severity, enabled, created_at, updated_at)
VALUES (NULL, :metric_name, :operator, :threshold_value, :severity, :enabled, NOW(), NOW());
```

**Purpose**: Inserts default threshold configuration values.

**Parameters**:
- `hostname`: NULL (global threshold)
- `metric_name`: Metric to monitor (e.g., 'cpu_percent')
- `operator`: Comparison operator (e.g., '>')
- `threshold_value`: Threshold value (e.g., 80.0)
- `severity`: Alert severity ('warning', 'critical')
- `enabled`: Boolean flag

**Default Thresholds**:
- CPU > 80% → warning
- CPU > 95% → critical
- Memory > 85% → warning
- Memory > 95% → critical
- Disk > 90% → warning

**When**: Runs on server startup if no global thresholds exist.

---

## Host Queries

### 6. List All Hosts with Status
**File**: `server/api_routes.py` (lines 35-56)

**Endpoint**: `GET /api/v1/hosts`

```sql
WITH latest_metrics AS (
    SELECT DISTINCT ON (hostname) 
        hostname,
        ip_address,
        timestamp as last_seen,
        CASE 
            WHEN (NOW() - timestamp) < INTERVAL '5 minutes' THEN 'online'
            ELSE 'offline'
        END as status
    FROM metrics 
    ORDER BY hostname, timestamp DESC
)
SELECT 
    hostname as host_id,
    hostname,
    COALESCE(ip_address, 'unknown') as ip_address,
    last_seen,
    status
FROM latest_metrics
ORDER BY hostname;
```

**Purpose**: Returns all monitored hosts with their latest connection status.

**Result Columns**:
- `host_id`: Host identifier
- `hostname`: Hostname
- `ip_address`: IP address (or 'unknown')
- `last_seen`: Last metric timestamp
- `status`: 'online' or 'offline' (based on 5-minute window)

**Logic**:
- Uses `DISTINCT ON (hostname)` to get the latest metric per host
- Calculates online/offline status based on last metric time
- Orders by hostname alphabetically

---

### 7. Host Existence Check
**File**: `server/api_routes.py` (line 190)

```sql
SELECT 1 FROM metrics WHERE hostname = :hostname LIMIT 1;
```

**Purpose**: Checks if a host exists in the metrics table.

**Used**: When historical metrics query returns no results (to determine if host exists).

---

## Metric Queries

### 8. Get Latest Metrics for Host
**File**: `server/api_routes.py` (lines 79-95)

**Endpoint**: `GET /api/v1/hosts/{host_id}/metrics/latest`

```sql
SELECT 
    hostname,
    timestamp,
    cpu_percent,
    mem_percent_used,
    disk_percent_used,
    net_bytes_sent,
    net_bytes_received,
    load_1m,
    load_5m,
    load_15m
FROM metrics 
WHERE hostname = :hostname 
ORDER BY timestamp DESC 
LIMIT 1;
```

**Purpose**: Retrieves the most recent metrics for a specific host.

**Returns**: Single row with latest metrics (CPU, memory, disk, network, load averages).

**Optimization**: Uses indexed `timestamp` column (primary key) for fast lookup.

---

### 9. Get Historical Metrics with Aggregation
**File**: `server/api_routes.py` (lines 162-173)

**Endpoint**: `GET /api/v1/hosts/{host_id}/metrics/historical/{metric_type}`

```sql
SELECT 
    EXTRACT(EPOCH FROM time_bucket(:interval, timestamp)) AS bucket_timestamp,
    AVG({metric_col}) AS avg_value
FROM metrics 
WHERE hostname = :hostname 
  AND timestamp >= :start_time 
  AND timestamp <= :end_time
  AND {metric_col} IS NOT NULL
GROUP BY time_bucket(:interval, timestamp)
ORDER BY bucket_timestamp;
```

**Purpose**: Retrieves time-series metrics with aggregation for graphs.

**Parameters**:
- `:interval`: Time bucket size (1m, 5m, 1h, 1d)
- `:hostname`: Host identifier
- `:start_time`: Start of time range
- `:end_time`: End of time range
- `{metric_col}`: Metric column name (validated from whitelist)

**Features**:
- Uses TimescaleDB `time_bucket()` function for aggregation
- Averages values within each time bucket
- Returns Unix timestamp for each bucket
- Filters out NULL values
- Ordered by time ascending

**Allowed Metric Types**:
- `cpu_percent`
- `mem_percent_used`
- `disk_percent_used`
- `net_bytes_sent`
- `net_bytes_received`
- `load_1m`, `load_5m`, `load_15m`

**Example**: Get hourly CPU averages for last 24 hours

```sql
SELECT 
    EXTRACT(EPOCH FROM time_bucket('1 hour', timestamp)) AS bucket_timestamp,
    AVG(cpu_percent) AS avg_value
FROM metrics 
WHERE hostname = 'server-01' 
  AND timestamp >= NOW() - INTERVAL '24 hours'
  AND timestamp <= NOW()
  AND cpu_percent IS NOT NULL
GROUP BY time_bucket('1 hour', timestamp)
ORDER BY bucket_timestamp;
```

---

## Alert Queries

Note: Most alert queries use SQLAlchemy ORM rather than raw SQL. Here are the key patterns:

### 10. Check for Existing Active Alert
**File**: `server/api_routes.py` (lines 323-329)

**SQLAlchemy Pattern**:
```python
select(models.Alert).where(
    and_(
        models.Alert.hostname == hostname,
        models.Alert.metric_name == metric_name,
        models.Alert.status == 'active'
    )
)
```

**Equivalent SQL**:
```sql
SELECT * FROM alerts
WHERE hostname = :hostname 
  AND metric_name = :metric_name
  AND status = 'active'
LIMIT 1;
```

**Purpose**: Prevents duplicate alerts for the same host/metric combination.

---

### 11. List Alerts with Filters
**File**: `server/api_routes.py` (lines 380-397)

**SQLAlchemy Pattern**:
```python
query = select(models.Alert)
if hostname:
    query = query.where(models.Alert.hostname == hostname)
if status:
    query = query.where(models.Alert.status == status)
if severity:
    query = query.where(models.Alert.severity == severity)

query = query.order_by(desc(models.Alert.triggered_at))
query = query.offset((page - 1) * limit).limit(limit)
```

**Equivalent SQL**:
```sql
SELECT * FROM alerts
WHERE (:hostname IS NULL OR hostname = :hostname)
  AND (:status IS NULL OR status = :status)
  AND (:severity IS NULL OR severity = :severity)
ORDER BY triggered_at DESC
LIMIT :limit OFFSET :offset;
```

**Purpose**: Retrieve paginated alerts with optional filters.

---

### 12. Get Alert by ID
**File**: `server/api_routes.py` (line 434)

**SQLAlchemy**:
```python
select(models.Alert).where(models.Alert.id == alert_id)
```

**Equivalent SQL**:
```sql
SELECT * FROM alerts WHERE id = :alert_id;
```

---

### 13. Count Active Alerts
**File**: `server/api_routes.py` (lines 469-472)

**SQLAlchemy**:
```python
select(func.count()).where(models.Alert.status == 'active')
```

**Equivalent SQL**:
```sql
SELECT COUNT(*) FROM alerts WHERE status = 'active';
```

---

### 14. Count Resolved Alerts
**File**: `server/api_routes.py` (lines 475-478)

**SQLAlchemy**:
```python
select(func.count()).where(models.Alert.status == 'resolved')
```

**Equivalent SQL**:
```sql
SELECT COUNT(*) FROM alerts WHERE status = 'resolved';
```

---

### 15. Count Alerts by Severity
**File**: `server/api_routes.py` (lines 481-486)

**SQLAlchemy**:
```python
select(models.Alert.severity, func.count())
.where(models.Alert.status == 'active')
.group_by(models.Alert.severity)
```

**Equivalent SQL**:
```sql
SELECT severity, COUNT(*) 
FROM alerts 
WHERE status = 'active'
GROUP BY severity;
```

**Result**: Returns counts for 'info', 'warning', 'critical' severities.

---

## Threshold Configuration Queries

### 16. Get All Global Thresholds
**File**: `server/api_routes.py` (lines 517-521)

**SQLAlchemy**:
```python
select(models.ThresholdConfig)
.where(models.ThresholdConfig.hostname.is_(None))
.order_by(models.ThresholdConfig.id)
```

**Equivalent SQL**:
```sql
SELECT * FROM threshold_configs
WHERE hostname IS NULL
ORDER BY id;
```

**Purpose**: Retrieve all global (non-host-specific) threshold configurations.

---

### 17. Delete All Global Thresholds
**File**: `server/api_routes.py` (lines 557, 604)

```sql
DELETE FROM threshold_configs WHERE hostname IS NULL;
```

**Purpose**: Removes all global threshold configurations (used before inserting new ones).

**When**: Called during threshold update and reset operations.

---

## Query Patterns with SQLAlchemy

### Pattern: Raw SQL with Parameters
```python
query = text("SELECT * FROM metrics WHERE hostname = :hostname")
result = await db.execute(query, {"hostname": "server-01"})
```

### Pattern: SQLAlchemy Select
```python
result = await db.execute(
    select(models.Metric)
    .where(models.Metric.hostname == hostname)
    .order_by(models.Metric.timestamp.desc())
    .limit(100)
)
```

### Pattern: COUNT with Subquery
```python
count_query = select(func.count()).select_from(query.subquery())
total_result = await db.execute(count_query)
total = total_result.scalar()
```

### Pattern: Aggregate with Group By
```python
result = await db.execute(
    select(
        models.Alert.severity,
        func.count()
    )
    .where(models.Alert.status == 'active')
    .group_by(models.Alert.severity)
)
```

---

## Performance Considerations

### Indexes Used
```sql
-- Metrics table (automatic from primary key)
PRIMARY KEY (timestamp, id)
INDEX ON hostname
INDEX ON timestamp

-- Alerts table
PRIMARY KEY (id)
INDEX ON hostname
INDEX ON metric_name
INDEX ON triggered_at
INDEX ON status

-- Thresholds table
PRIMARY KEY (id)
INDEX ON hostname
```

### TimescaleDB Optimizations

**Partition Pruning**: Queries automatically scan only relevant time partitions.

```sql
-- Only scans partitions containing data in the date range
SELECT * FROM metrics 
WHERE timestamp > '2024-01-01' 
  AND timestamp < '2024-01-02';
```

**time_bucket() Function**: Efficient aggregation for time-series data.

```sql
-- Averages metrics in 1-hour buckets
SELECT time_bucket('1 hour', timestamp), AVG(cpu_percent)
FROM metrics
GROUP BY time_bucket('1 hour', timestamp);
```

**Continuous Aggregates** (future enhancement):

```sql
-- Pre-compute hourly averages
CREATE MATERIALIZED VIEW hourly_cpu_avg AS
SELECT 
    hostname,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(cpu_percent) AS avg_cpu
FROM metrics
GROUP BY hostname, hour;
```

---

## Query Response Times

**Estimated performance** (with TimescaleDB hypertable):

| Query Type | Rows Scanned | Response Time |
|------------|--------------|---------------|
| Latest metrics | ~100 (partition) | < 50ms |
| Historical (1 hour) | ~360 | < 100ms |
| Historical (24 hours) | ~8,640 | < 200ms |
| Historical (7 days) | ~60,480 | < 500ms |
| Host list with status | ~10,000 | < 100ms |
| Alert list (paginated) | ~1,000 | < 50ms |
| Alert statistics | Full table | < 200ms |

**Note**: TimescaleDB partitioning dramatically improves query performance for large datasets.

---

## SQL Injection Prevention

### Whitelist Validation
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

# Only allow whitelisted metric types
if metric_type not in ALLOWED_METRIC_TYPES:
    raise HTTPException(400, "Invalid metric_type")
```

### Parameterized Queries
```python
# ✅ Safe: Uses parameters
query = text("SELECT * FROM metrics WHERE hostname = :hostname")
await db.execute(query, {"hostname": user_input})

# ❌ Unsafe: String concatenation
query = f"SELECT * FROM metrics WHERE hostname = '{user_input}'"
```

---

## Future SQL Queries

### Potential Enhancements

**1. Advanced Time-Series Queries**:
```sql
-- Moving averages
SELECT 
    hostname,
    timestamp,
    cpu_percent,
    AVG(cpu_percent) OVER (PARTITION BY hostname ORDER BY timestamp ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) as moving_avg
FROM metrics;
```

**2. Historical Comparisons**:
```sql
-- Compare current CPU with same time yesterday
SELECT 
    current_timestamp,
    current_cpu,
    yesterday_cpu,
    current_cpu - yesterday_cpu as delta
FROM (
    SELECT AVG(cpu_percent) as current_cpu 
    FROM metrics 
    WHERE timestamp > NOW() - INTERVAL '1 hour'
) current
CROSS JOIN (
    SELECT AVG(cpu_percent) as yesterday_cpu 
    FROM metrics 
    WHERE timestamp > NOW() - INTERVAL '25 hours' 
      AND timestamp < NOW() - INTERVAL '24 hours'
) yesterday;
```

**3. Alert Frequency Analysis**:
```sql
-- Alerts per hour
SELECT 
    DATE_TRUNC('hour', triggered_at) as hour,
    COUNT(*) as alert_count
FROM alerts
WHERE triggered_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## References

- **TimescaleDB Documentation**: https://docs.timescale.com/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Server Routes**: `server/api_routes.py`
- **Database Setup**: `server/app.py`, `server/database.py`

