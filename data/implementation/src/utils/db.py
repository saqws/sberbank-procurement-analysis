"""Database connection and utilities."""
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
from src.utils.config import settings
from src.utils.logger import logger

# Create engine
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def execute_sql_file(sql_file: str):
    """Execute SQL file."""
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    with get_db() as db:
        db.execute(text(sql))
        logger.info(f"Executed SQL file: {sql_file}")

def test_connection() -> bool:
    """Test database connection."""
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
