"""Configuration management module."""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseSettings, Field

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = Field(default="postgresql://postgres:password@localhost:5432/procurement", env="DATABASE_URL")
    
    # API Keys
    eis_api_key: str = Field(default="", env="EIS_API_KEY")
    spark_api_key: str = Field(default="", env="SPARK_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    
    # Scraping
    selenium_hub_url: str = Field(default="http://localhost:4444/wd/hub", env="SELENIUM_HUB_URL")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="USER_AGENT"
    )
    
    # Rate Limiting
    eis_requests_per_minute: int = Field(default=30, env="EIS_REQUESTS_PER_MINUTE")
    commercial_delay_seconds: int = Field(default=2, env="COMMERCIAL_DELAY_SECONDS")
    
    # Data Collection
    start_date: str = Field(default="2024-01-01", env="START_DATE")
    end_date: str = Field(default="2025-12-31", env="END_DATE")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/procurement.log", env="LOG_FILE")
    
    # Analysis
    anomaly_threshold: float = Field(default=0.05, env="ANOMALY_THRESHOLD")
    correlation_min_threshold: float = Field(default=0.3, env="CORRELATION_MIN_THRESHOLD")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = base_dir / "data"
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    external_data_dir: Path = data_dir / "external"
    documents_dir: Path = data_dir / "documents"
    logs_dir: Path = base_dir / "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure directories exist
settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
settings.external_data_dir.mkdir(parents=True, exist_ok=True)
settings.documents_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)
