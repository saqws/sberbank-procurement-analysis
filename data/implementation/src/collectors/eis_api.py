"""EIS (zakupki.gov.ru) API client."""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.config import settings
from src.utils.logger import logger
from tqdm import tqdm

class EISClient:
    """Client for EIS API (zakupki.gov.ru)."""
    
    BASE_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"
    API_URL = "https://zakupki.gov.ru/epz/opendata/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.eis_api_key
        self.session = None
        self.rate_limit = settings.eis_requests_per_minute
        self.request_interval = 60 / self.rate_limit
        self.last_request_time = datetime.now()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": settings.user_agent,
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _wait_for_rate_limit(self):
        """Ensure rate limit compliance."""
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.request_interval:
            await asyncio.sleep(self.request_interval - elapsed)
        self.last_request_time = datetime.now()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_request(self, url: str, params: Dict) -> Dict:
        """Make API request with retry logic."""
        await self._wait_for_rate_limit()
        
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def search_procurements(
        self,
        customer_inn: str,
        start_date: str,
        end_date: str,
        law_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Dict:
        """
        Search procurements by customer INN and date range.
        
        Args:
            customer_inn: Customer INN
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            law_type: 44-FZ or 223-FZ
            page: Page number
            per_page: Results per page
        
        Returns:
            API response with procurements list
        """
        params = {
            "customerINN": customer_inn,
            "publishDateFrom": start_date,
            "publishDateTo": end_date,
            "pageNumber": page,
            "recordsPerPage": per_page,
            "sortBy": "UPDATE_DATE",
            "sortDirection": "DESC"
        }
        
        if law_type:
            params["fz"] = law_type.replace("-", "")
        
        try:
            data = await self._make_request(f"{self.API_URL}/contracts/search", params)
            logger.info(f"Fetched page {page} for INN {customer_inn}: {len(data.get('contracts', []))} records")
            return data
        except Exception as e:
            logger.error(f"Error fetching procurements for INN {customer_inn}: {e}")
            return {"contracts": [], "total": 0}
    
    async def get_procurement_details(self, procurement_id: str) -> Optional[Dict]:
        """Get detailed information about specific procurement."""
        try:
            data = await self._make_request(
                f"{self.API_URL}/contracts/{procurement_id}",
                {}
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching procurement {procurement_id}: {e}")
            return None
    
    async def get_procurement_documents(self, procurement_id: str) -> List[Dict]:
        """Get documents for specific procurement."""
        try:
            data = await self._make_request(
                f"{self.API_URL}/contracts/{procurement_id}/documents",
                {}
            )
            return data.get("documents", [])
        except Exception as e:
            logger.error(f"Error fetching documents for {procurement_id}: {e}")
            return []
    
    async def collect_for_organizations(
        self,
        inn_list: List[str],
        start_date: str,
        end_date: str,
        output_file: str = "data/raw/eis/procurements.json"
    ) -> List[Dict]:
        """
        Collect all procurements for list of organizations.
        
        Args:
            inn_list: List of customer INNs
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            output_file: Output JSON file path
        
        Returns:
            List of all procurements
        """
        all_procurements = []
        
        with tqdm(total=len(inn_list), desc="Collecting from EIS") as pbar:
            for inn in inn_list:
                page = 1
                while True:
                    data = await self.search_procurements(
                        customer_inn=inn,
                        start_date=start_date,
                        end_date=end_date,
                        page=page,
                        per_page=100
                    )
                    
                    contracts = data.get("contracts", [])
                    if not contracts:
                        break
                    
                    # Enrich with source info
                    for contract in contracts:
                        contract["source"] = "eis"
                        contract["collected_at"] = datetime.now().isoformat()
                    
                    all_procurements.extend(contracts)
                    
                    # Check if more pages
                    if len(contracts) < 100:
                        break
                    
                    page += 1
                
                pbar.update(1)
        
        logger.info(f"Collected {len(all_procurements)} procurements from EIS")
        
        # Save to file
        import json
        from pathlib import Path
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_procurements, f, ensure_ascii=False, indent=2)
        
        return all_procurements


async def main():
    """Example usage."""
    # Test with single organization
    test_inns = ["7707083893"]  # Sberbank INN
    
    async with EISClient() as client:
        procurements = await client.collect_for_organizations(
            inn_list=test_inns,
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        print(f"Collected {len(procurements)} procurements")


if __name__ == "__main__":
    asyncio.run(main())
