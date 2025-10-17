import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# This is the connection string for your database.
# It reads from an environment variable or uses a default value.
# Make sure to replace 'password' if you changed it in the docker command.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/postgres")

# The engine is the core interface to the database.
engine = create_async_engine(DATABASE_URL)

# A sessionmaker creates new database sessions for each request.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# This is a base class that our table models will inherit from.
Base = declarative_base()

# This function will be used by FastAPI to inject a database session into your endpoints.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session