# in server/app.py
import os
import uvicorn
from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Import the new modules we created
from server import models
from server.database import engine, get_db
from server.pydantic_models import MetricPayload
from server import api_routes

# --- FastAPI Application Setup ---
app = FastAPI(
    title="SysSight Server",
    description="The central server for collecting and managing host metrics."
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_routes.router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    # This function runs once when the server starts.
    print("Initializing database...")
    async with engine.begin() as conn:
        # Create all the tables defined in models.py if they don't exist.
        await conn.run_sync(models.Base.metadata.create_all)

        # Ensure new columns exist (safe to run repeatedly)
        await conn.execute(text("ALTER TABLE public.metrics ADD COLUMN IF NOT EXISTS ip_address VARCHAR;"))

        # Ensure PK conforms to Timescale requirement (timestamp in PK)
        await conn.execute(text("""
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
        """))

        # Convert to hypertable (idempotent)
        await conn.execute(text("SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);"))
    print("Database initialization complete.")

# --- Dependency for Authentication ---
async def verify_token(authorization: str = Header(...)):
    expected_token = os.getenv("SYSSIGHT_AUTH_TOKEN", "your_secret_auth_token")
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")

# --- API Endpoint to Save Metrics ---
@app.post("/metrics", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
async def receive_and_save_metrics(payload: MetricPayload, db: AsyncSession = Depends(get_db)):
    """
    Receives, validates, and saves metrics from an agent to the database.
    """
    # Create a new database model object from the incoming data.
    new_metric = models.Metric(
        hostname=payload.hostname,
        timestamp=payload.timestamp,
        cpu_percent=payload.cpu_percent,
        mem_percent_used=payload.memory.percent_used,
        disk_percent_used=payload.disk.percent_used,
        net_bytes_sent=payload.network.bytes_sent,
        net_bytes_received=payload.network.bytes_received,
        load_1m=payload.load_average.m1,
        load_5m=payload.load_average.m5,
        load_15m=payload.load_average.m15,
        ip_address=payload.ip_address,
    )
    
    # Add the new metric to the session and commit it to the database.
    db.add(new_metric)
    await db.commit()
    await db.refresh(new_metric)
    
    print(f"Successfully saved metric ID {new_metric.id} for host {new_metric.hostname}")

    return {"status": "success", "message": f"Metric ID {new_metric.id} saved"}

# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)