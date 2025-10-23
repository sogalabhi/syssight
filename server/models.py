from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Text, Boolean
from .database import Base

class Metric(Base):
    __tablename__ = "metrics"

    # Timescale requires UNIQUE/PK to include the partitioning key (timestamp)
    # Use a composite primary key (timestamp, id)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True, index=True)
    hostname = Column(String, index=True)
    ip_address = Column(String, nullable=True)

    # We'll store the key metrics needed for graphing.
    cpu_percent = Column(Float)
    mem_percent_used = Column(Float)
    disk_percent_used = Column(Float)
    net_bytes_sent = Column(BigInteger)
    net_bytes_received = Column(BigInteger)
    load_1m = Column(Float)
    load_5m = Column(Float)
    load_15m = Column(Float)

class Process(Base):
    __tablename__ = "processes"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True, index=True)
    hostname = Column(String, index=True)
    
    # Process information
    pid = Column(Integer, index=True)
    name = Column(String)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)

class ThresholdConfig(Base):
    __tablename__ = "threshold_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String, index=True, nullable=True)  # null = global default
    metric_name = Column(String)  # cpu_percent, mem_percent_used, etc.
    operator = Column(String)  # >, <, >=, <=, ==
    threshold_value = Column(Float)
    severity = Column(String)  # info, warning, critical
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String, index=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    threshold_value = Column(Float)
    severity = Column(String)
    status = Column(String, default='active')  # active, resolved, acknowledged
    message = Column(Text)
    triggered_at = Column(DateTime(timezone=True), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)