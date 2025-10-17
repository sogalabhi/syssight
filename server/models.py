from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from .database import Base

class Metric(Base):
    __tablename__ = "metrics"

    # Timescale requires UNIQUE/PK to include the partitioning key (timestamp)
    # Use a composite primary key (timestamp, id)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True, index=True)
    hostname = Column(String, index=True)

    # We'll store the key metrics needed for graphing.
    cpu_percent = Column(Float)
    mem_percent_used = Column(Float)
    disk_percent_used = Column(Float)
    net_bytes_sent = Column(BigInteger)
    net_bytes_received = Column(BigInteger)
    load_1m = Column(Float)
    load_5m = Column(Float)
    load_15m = Column(Float)