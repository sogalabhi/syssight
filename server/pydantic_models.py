from pydantic import BaseModel, Field
from typing import Optional
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

