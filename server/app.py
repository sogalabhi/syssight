import os
import uvicorn
from fastapi import FastAPI, Request, status, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# --- Pydantic Models for Data Validation ---

class LoadAverage(BaseModel):
    m1: float = Field(..., alias='1m')
    m5: float = Field(..., alias='5m')
    m15: float = Field(..., alias='15m')
    m1_normalized: float = Field(..., alias='1m_normalized')
    m5_normalized: float = Field(..., alias='5m_normalized')
    m15_normalized: float = Field(..., alias='15m_normalized')

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
    timestamp: str
    cpu_percent: float
    load_average: LoadAverage
    disk: DiskInfo
    memory: MemoryInfo
    network: NetworkIO
    process_count: Optional[int] = None

EXPECTED_AUTH_TOKEN = os.getenv("SYSSIGHT_AUTH_TOKEN", "your_secret_auth_token")

app = FastAPI(
    title="SysSight Server",
    description="The central server for collecting and managing host metrics."
)

async def verify_token(authorization: str = Header(...)):
    if authorization != f"Bearer {EXPECTED_AUTH_TOKEN}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")

# API Endpoints 
@app.post("/metrics", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
async def receive_metrics(payload: MetricPayload):
    """
    Receives, validates, and processes metrics from a SysSight agent.
    """
    print("\n" + "="*50)
    print(f"Received metrics from: {payload.hostname} at {payload.timestamp}")
    print(payload.dict(by_alias=True)) # Use by_alias to print '1m' correctly
    print("="*50)

    return {"status": "success", "message": "Metrics received"}

# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)