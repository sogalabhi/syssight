from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, desc, and_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import time
import requests
import math

from .database import get_db
from . import models
from .pydantic_models import AlertPayload, AlertResponse, AlertListResponse, AlertStatsResponse, ThresholdConfigItem, ThresholdConfigResponse, ThresholdConfigUpdate
from . import discord_notifier

router = APIRouter()

# Allowed metric types for historical queries (prevent SQL injection)
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

@router.get("/hosts")
async def list_hosts(db: AsyncSession = Depends(get_db)):
    """
    List all monitored hosts with their status and last seen timestamp.
    """
    # Query to get distinct hosts with their latest metrics and status
    query = text("""
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
        ORDER BY hostname
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    hosts = []
    for row in rows:
        hosts.append({
            "host_id": row.host_id,
            "hostname": row.hostname,
            "ip_address": row.ip_address,
            "last_seen": row.last_seen.isoformat() + "Z" if row.last_seen else None,
            "status": row.status
        })
    
    return hosts

@router.get("/hosts/{host_id}/metrics/latest")
async def get_latest_metrics(host_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the latest metrics for a specific host.
    """
    # Query the most recent metric for the given host
    query = text("""
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
        LIMIT 1
    """)
    
    result = await db.execute(query, {"hostname": host_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    
    return {
        "host_id": row.hostname,
        "timestamp": row.timestamp.isoformat() + "Z",
        "cpu_percent": row.cpu_percent,
        "memory_percent": row.mem_percent_used,
        "disk_usage": {
            "/": {"percent": row.disk_percent_used}
        },
        "network": {
            "bytes_sent": row.net_bytes_sent,
            "bytes_recv": row.net_bytes_received
        },
        "load_average": [row.load_1m, row.load_5m, row.load_15m]
    }

@router.get("/hosts/{host_id}/metrics/historical/{metric_type}")
async def get_historical_metrics(
    host_id: str,
    metric_type: str,
    start_time: str = Query(..., description="Start time in ISO 8601 format"),
    end_time: str = Query(..., description="End time in ISO 8601 format"),
    step: str = Query("1m", description="Aggregation step (1m, 5m, 1h)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical metrics for a specific host and metric type with time aggregation.
    """
    # Validate metric type
    if metric_type not in ALLOWED_METRIC_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric_type '{metric_type}'. Allowed: {', '.join(ALLOWED_METRIC_TYPES)}"
        )
    
    # Parse step into a Python timedelta so asyncpg encodes a proper SQL interval
    step_mapping = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5), 
        "1h": timedelta(hours=1),
        "1d": timedelta(days=1)
    }
    
    if step not in step_mapping:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step '{step}'. Allowed: {', '.join(step_mapping.keys())}"
        )
    
    interval = step_mapping[step]
    
    # Parse timestamps
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO 8601 format.")
    
    # Build query with validated metric column name interpolated
    metric_col = metric_type  # safe due to whitelist above
    query_sql = f"""
        SELECT 
            EXTRACT(EPOCH FROM time_bucket(:interval, timestamp)) AS bucket_timestamp,
            AVG({metric_col}) AS avg_value
        FROM metrics 
        WHERE hostname = :hostname 
          AND timestamp >= :start_time 
          AND timestamp <= :end_time
          AND {metric_col} IS NOT NULL
        GROUP BY time_bucket(:interval, timestamp)
        ORDER BY bucket_timestamp
    """

    result = await db.execute(
        text(query_sql),
        {
            "hostname": host_id,
            "interval": interval,
            "start_time": start_dt,
            "end_time": end_dt,
        },
    )
    
    rows = result.fetchall()
    
    if not rows:
        # Check if host exists at all
        host_check = await db.execute(
            text("SELECT 1 FROM metrics WHERE hostname = :hostname LIMIT 1"),
            {"hostname": host_id}
        )
        if not host_check.fetchone():
            raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    
    values = []
    for row in rows:
        # Convert to integer timestamp and round value
        timestamp = int(row.bucket_timestamp)
        value = round(float(row.avg_value), 2) if row.avg_value is not None else None
        if value is not None:
            values.append([timestamp, value])
    
    return {
        "metric_type": metric_type,
        "values": values
    }

# Import agent registry from separate module
from .agent_registry import agent_registry

@router.post("/agents/register")
async def register_agent(registration_data: dict):
    """
    Register an agent with its IP address and port.
    """
    try:
        hostname = registration_data.get("hostname")
        ip_address = registration_data.get("ip_address")
        port = registration_data.get("port")
        
        if not all([hostname, ip_address, port]):
            raise HTTPException(status_code=400, detail="Missing required fields: hostname, ip_address, port")
        
        # Store in registry as "ip:port"
        agent_registry[hostname] = f"{ip_address}:{port}"
        
        print(f"Agent registered: {hostname} -> {ip_address}:{port}")
        print(f"Current registry: {agent_registry}")
        
        return {
            "status": "success",
            "message": f"Agent {hostname} registered at {ip_address}:{port}"
        }
    except Exception as e:
        print(f"Agent registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.get("/agents")
async def list_agents():
    """
    List all registered agents.
    """
    return {
        "agents": agent_registry,
        "count": len(agent_registry)
    }

@router.get("/hosts/{hostname}/processes")
async def get_host_processes(
    hostname: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("cpu_percent", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    Get paginated process list for a specific host.
    """
    # Validate sort parameters
    allowed_sort_fields = {"cpu_percent", "memory_percent", "pid", "name"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Must be one of: {allowed_sort_fields}")
    
    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="sort_order must be 'asc' or 'desc'")
    
    # Look up agent in registry
    if hostname not in agent_registry:
        print(f"⚠️  Agent '{hostname}' not found in registry. Current agents: {list(agent_registry.keys())}")
        raise HTTPException(
            status_code=404, 
            detail=f"Agent '{hostname}' not registered. Available agents: {list(agent_registry.keys())}"
        )
    
    agent_address = agent_registry[hostname]
    agent_url = f"http://{agent_address}/processes"
    
    try:
        # Fetch process list from agent
        response = requests.get(agent_url, timeout=10)
        response.raise_for_status()
        processes = response.json()
        
        if not isinstance(processes, list):
            raise HTTPException(status_code=500, detail="Invalid response from agent")
        
        # Sort processes
        reverse = sort_order == "desc"
        processes.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        # Calculate pagination
        total = len(processes)
        total_pages = math.ceil(total / limit)
        start = (page - 1) * limit
        end = start + limit
        
        # Get page slice
        page_processes = processes[start:end]
        
        return {
            "processes": page_processes,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to agent: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Alert Management Endpoints

@router.post("/alerts")
async def create_alert(alert: AlertPayload, db: AsyncSession = Depends(get_db)):
    """
    Create a new alert. Checks for existing active alerts to prevent duplicates.
    """
    # Check for existing active alert with same hostname + metric
    existing_alert = await db.execute(
        select(models.Alert).where(
            and_(
                models.Alert.hostname == alert.hostname,
                models.Alert.metric_name == alert.metric_name,
                models.Alert.status == 'active'
            )
        )
    )
    existing = existing_alert.scalar_one_or_none()
    
    if existing:
        # Update existing alert timestamp
        existing.triggered_at = alert.timestamp
        await db.commit()
        return {"status": "updated", "alert_id": existing.id}
    else:
        # Create new alert
        new_alert = models.Alert(
            hostname=alert.hostname,
            metric_name=alert.metric_name,
            metric_value=alert.metric_value,
            threshold_value=alert.threshold_value,
            severity=alert.severity,
            message=alert.message,
            triggered_at=alert.timestamp
        )
        db.add(new_alert)
        await db.commit()
        await db.refresh(new_alert)
        
        # Send Discord notification
        discord_notifier.send_alert_notification(
            alert_id=new_alert.id,
            hostname=new_alert.hostname,
            metric_name=new_alert.metric_name,
            metric_value=new_alert.metric_value,
            threshold_value=new_alert.threshold_value,
            severity=new_alert.severity,
            message=new_alert.message,
            triggered_at=new_alert.triggered_at
        )
        
        return {"status": "created", "alert_id": new_alert.id}

@router.get("/alerts")
async def list_alerts(
    hostname: Optional[str] = Query(None, description="Filter by hostname"),
    status: Optional[str] = Query(None, description="Filter by status (active, resolved, acknowledged)"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List alerts with optional filtering and pagination.
    """
    # Build query with filters
    query = select(models.Alert)
    
    if hostname:
        query = query.where(models.Alert.hostname == hostname)
    if status:
        query = query.where(models.Alert.status == status)
    if severity:
        query = query.where(models.Alert.severity == severity)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(desc(models.Alert.triggered_at))
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Convert to response format
    alert_responses = []
    for alert in alerts:
        alert_responses.append(AlertResponse(
            id=alert.id,
            hostname=alert.hostname,
            metric_name=alert.metric_name,
            metric_value=alert.metric_value,
            threshold_value=alert.threshold_value,
            severity=alert.severity,
            status=alert.status,
            message=alert.message,
            triggered_at=alert.triggered_at,
            resolved_at=alert.resolved_at,
            resolved_by=alert.resolved_by
        ))
    
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return AlertListResponse(
        alerts=alert_responses,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mark an alert as resolved.
    """
    # Get the alert
    result = await db.execute(select(models.Alert).where(models.Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.status == 'resolved':
        raise HTTPException(status_code=400, detail="Alert already resolved")
    
    # Update alert status
    alert.status = 'resolved'
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = 'system'  # In a real app, this would be the current user
    
    await db.commit()
    
    # Send Discord resolution notification
    discord_notifier.send_resolution_notification(
        alert_id=alert.id,
        hostname=alert.hostname,
        metric_name=alert.metric_name,
        severity=alert.severity,
        triggered_at=alert.triggered_at,
        resolved_at=alert.resolved_at,
        resolved_by=alert.resolved_by
    )
    
    return {"status": "success", "message": f"Alert {alert_id} resolved"}

@router.get("/alerts/stats")
async def get_alert_stats(db: AsyncSession = Depends(get_db)):
    """
    Get alert statistics summary.
    """
    # Count active alerts
    active_result = await db.execute(
        select(func.count()).where(models.Alert.status == 'active')
    )
    active_count = active_result.scalar()
    
    # Count resolved alerts
    resolved_result = await db.execute(
        select(func.count()).where(models.Alert.status == 'resolved')
    )
    resolved_count = resolved_result.scalar()
    
    # Count by severity
    severity_result = await db.execute(
        select(models.Alert.severity, func.count())
        .where(models.Alert.status == 'active')
        .group_by(models.Alert.severity)
    )
    by_severity = {row[0]: row[1] for row in severity_result.fetchall()}
    
    # Ensure all severities are present
    for severity in ['info', 'warning', 'critical']:
        if severity not in by_severity:
            by_severity[severity] = 0
    
    return AlertStatsResponse(
        active_count=active_count,
        resolved_count=resolved_count,
        by_severity=by_severity
    )

# Threshold Configuration Endpoints

# Default thresholds matching agent.py hardcoded defaults
DEFAULT_THRESHOLDS = [
    {'metric_name': 'cpu_percent', 'operator': '>', 'threshold_value': 80.0, 'severity': 'warning', 'enabled': True},
    {'metric_name': 'cpu_percent', 'operator': '>', 'threshold_value': 95.0, 'severity': 'critical', 'enabled': True},
    {'metric_name': 'mem_percent_used', 'operator': '>', 'threshold_value': 85.0, 'severity': 'warning', 'enabled': True},
    {'metric_name': 'mem_percent_used', 'operator': '>', 'threshold_value': 95.0, 'severity': 'critical', 'enabled': True},
    {'metric_name': 'disk_percent_used', 'operator': '>', 'threshold_value': 90.0, 'severity': 'warning', 'enabled': True},
]

@router.get("/thresholds", response_model=ThresholdConfigResponse)
async def get_thresholds(db: AsyncSession = Depends(get_db)):
    """
    Get all global threshold configurations.
    Returns hardcoded defaults if database is empty.
    """
    # Fetch global thresholds (where hostname IS NULL)
    result = await db.execute(
        select(models.ThresholdConfig)
        .where(models.ThresholdConfig.hostname.is_(None))
        .order_by(models.ThresholdConfig.id)
    )
    thresholds = result.scalars().all()
    
    # If no thresholds in database, return defaults
    if not thresholds:
        threshold_items = [
            ThresholdConfigItem(**t) for t in DEFAULT_THRESHOLDS
        ]
        return ThresholdConfigResponse(thresholds=threshold_items)
    
    # Convert to response format
    threshold_items = [
        ThresholdConfigItem(
            id=t.id,
            metric_name=t.metric_name,
            operator=t.operator,
            threshold_value=t.threshold_value,
            severity=t.severity,
            enabled=t.enabled
        )
        for t in thresholds
    ]
    
    return ThresholdConfigResponse(thresholds=threshold_items)

@router.put("/thresholds", response_model=ThresholdConfigResponse)
async def update_thresholds(
    update: ThresholdConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update all global threshold configurations.
    Replaces existing thresholds with new ones.
    """
    # Delete existing global thresholds
    await db.execute(
        text("DELETE FROM threshold_configs WHERE hostname IS NULL")
    )
    
    # Insert new thresholds
    new_thresholds = []
    for threshold in update.thresholds:
        new_threshold = models.ThresholdConfig(
            hostname=None,  # Global threshold
            metric_name=threshold.metric_name,
            operator=threshold.operator,
            threshold_value=threshold.threshold_value,
            severity=threshold.severity,
            enabled=threshold.enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_threshold)
        new_thresholds.append(new_threshold)
    
    await db.commit()
    
    # Refresh to get IDs
    for t in new_thresholds:
        await db.refresh(t)
    
    # Return updated thresholds
    threshold_items = [
        ThresholdConfigItem(
            id=t.id,
            metric_name=t.metric_name,
            operator=t.operator,
            threshold_value=t.threshold_value,
            severity=t.severity,
            enabled=t.enabled
        )
        for t in new_thresholds
    ]
    
    return ThresholdConfigResponse(thresholds=threshold_items)

@router.post("/thresholds/reset", response_model=ThresholdConfigResponse)
async def reset_thresholds(db: AsyncSession = Depends(get_db)):
    """
    Reset global thresholds to hardcoded defaults.
    """
    # Delete existing global thresholds
    await db.execute(
        text("DELETE FROM threshold_configs WHERE hostname IS NULL")
    )
    
    # Insert default thresholds
    new_thresholds = []
    for threshold in DEFAULT_THRESHOLDS:
        new_threshold = models.ThresholdConfig(
            hostname=None,
            metric_name=threshold['metric_name'],
            operator=threshold['operator'],
            threshold_value=threshold['threshold_value'],
            severity=threshold['severity'],
            enabled=threshold['enabled'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_threshold)
        new_thresholds.append(new_threshold)
    
    await db.commit()
    
    # Refresh to get IDs
    for t in new_thresholds:
        await db.refresh(t)
    
    # Return default thresholds
    threshold_items = [
        ThresholdConfigItem(
            id=t.id,
            metric_name=t.metric_name,
            operator=t.operator,
            threshold_value=t.threshold_value,
            severity=t.severity,
            enabled=t.enabled
        )
        for t in new_thresholds
    ]
    
    return ThresholdConfigResponse(thresholds=threshold_items)
