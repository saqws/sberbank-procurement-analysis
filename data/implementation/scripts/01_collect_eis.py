#!/usr/bin/env python3
"""Collect data from EIS (zakupki.gov.ru)."""
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.eis_api import EISClient
from src.utils.logger import logger
from src.utils.config import settings

async def main():
    """Main collection script."""
    logger.info("Starting EIS data collection...")
    
    # Load Sberbank organizations
    org_file = Path(__file__).parent.parent / "data" / "sberbank_organizations.json"
    with open(org_file, 'r', encoding='utf-8') as f:
        organizations = json.load(f)
    
    inn_list = [org['inn'] for org in organizations if org.get('is_sber_group')]
    logger.info(f"Loaded {len(inn_list)} Sberbank organizations")
    
    # Collect data
    async with EISClient() as client:
        procurements = await client.collect_for_organizations(
            inn_list=inn_list,
            start_date=settings.start_date,
            end_date=settings.end_date,
            output_file="data/raw/eis/procurements.json"
        )
    
    logger.info(f"Collection complete: {len(procurements)} procurements")
    logger.info(f"Data saved to: data/raw/eis/procurements.json")

if __name__ == "__main__":
    asyncio.run(main())
