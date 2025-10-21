from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import time
import requests
import math

from .database import get_db
from . import models

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
from server.agent_registry import agent_registry

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
        
        return {
            "status": "success",
            "message": f"Agent {hostname} registered at {ip_address}:{port}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

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
        raise HTTPException(status_code=404, detail=f"Agent '{hostname}' not registered")
    
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
