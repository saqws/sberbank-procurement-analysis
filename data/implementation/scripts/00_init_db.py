#!/usr/bin/env python3
"""Initialize database schema."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.db import test_connection, execute_sql_file
from src.utils.logger import logger

def main():
    """Initialize database."""
    logger.info("Initializing database...")
    
    # Test connection
    if not test_connection():
        logger.error("Database connection failed. Check your .env configuration.")
        sys.exit(1)
    
    # Execute schema
    schema_file = Path(__file__).parent.parent / "sql" / "schema.sql"
    if schema_file.exists():
        execute_sql_file(str(schema_file))
        logger.info("Database schema created successfully")
    else:
        logger.error(f"Schema file not found: {schema_file}")
        sys.exit(1)
    
    logger.info("Database initialization complete")

if __name__ == "__main__":
    main()
