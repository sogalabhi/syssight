from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LoadAverage(BaseModel):
    m1: float = Field(..., alias='1m')
    m5: float = Field(..., alias='5m')
    m15: float = Field(..., alias='15m')


class DiskInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float


class MemoryInfo(BaseModel):
    total_gb: float
    available_gb: float
    percent_used: float


class NetworkIO(BaseModel):
    bytes_sent: int
    bytes_received: int


class MetricPayload(BaseModel):
    hostname: str
    # Accept both string and datetime; FastAPI will parse ISO8601 into datetime
    timestamp: datetime
    cpu_percent: float
    load_average: LoadAverage
    disk: DiskInfo
    memory: MemoryInfo
    network: NetworkIO
    process_count: Optional[int] = None
    ip_address: Optional[str] = None

    class Config:
        populate_by_name = True

class AlertPayload(BaseModel):
    hostname: str
    metric_name: str
    metric_value: float
    threshold_value: float
    severity: str
    message: str
    timestamp: datetime

class ThresholdConfigPayload(BaseModel):
    hostname: Optional[str] = None
    metric_name: str
    operator: str
    threshold_value: float
    severity: str
    enabled: bool = True

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

class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    limit: int
    total_pages: int

class AlertStatsResponse(BaseModel):
    active_count: int
    resolved_count: int
    by_severity: dict

# Threshold Configuration Models
class ThresholdConfigItem(BaseModel):
    id: Optional[int] = None
    metric_name: str
    operator: str
    threshold_value: float
    severity: str
    enabled: bool = True
    
class ThresholdConfigResponse(BaseModel):
    thresholds: List[ThresholdConfigItem]
    
class ThresholdConfigUpdate(BaseModel):
    thresholds: List[ThresholdConfigItem]

