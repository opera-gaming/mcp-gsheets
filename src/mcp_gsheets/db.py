import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mcpuser:mcppassword@localhost:5432/mcp_gsheets')

# Create engine with connection pool configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Maximum number of connections to keep in the pool
    max_overflow=20,       # Maximum number of connections that can be created beyond pool_size
    pool_pre_ping=True,    # Verify connections before using them (detect stale connections)
    pool_recycle=3600      # Recycle connections after 1 hour to prevent stale connections
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
