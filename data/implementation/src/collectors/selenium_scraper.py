"""Selenium scraper for commercial ETP platforms."""
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.utils.config import settings
from src.utils.logger import logger
from tqdm import tqdm

class CommercialETPScraper:
    """Scraper for commercial electronic trading platforms."""
    
    PLATFORMS = {
        "sberbank-ast": {
            "url": "https://www.sberbank-ast.ru/purchaseList.aspx",
            "name": "Сбербанк-АСТ"
        },
        "etpgpb": {
            "url": "https://etpgpb.ru/procedures/tenders/list",
            "name": "ЕТП ГПБ"
        },
        "rts-tender": {
            "url": "https://rts-tender.ru/Trade/Search.aspx",
            "name": "РТС-тендер"
        },
        "roseltorg": {
            "url": "https://roseltorg.ru/procedures",
            "name": "Росэлторг"
        },
        "lot-online": {
            "url": "https://lot-online.ru/Trade/Search",
            "name": "ЛотОнлайн"
        }
    }
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome driver."""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={settings.user_agent}")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
    
    def __enter__(self):
        self._init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()
    
    def scrape_sberbank_ast(
        self,
        search_query: str = "Сбербанк",
        max_pages: int = 10
    ) -> List[Dict]:
        """Scrape Sberbank-AST platform."""
        logger.info("Scraping Sberbank-AST...")
        procurements = []
        
        try:
            self.driver.get(self.PLATFORMS["sberbank-ast"]["url"])
            
            # Search
            search_input = self.driver.find_element(By.ID, "ctl00_Content_txtSearch")
            search_input.send_keys(search_query)
            search_btn = self.driver.find_element(By.ID, "ctl00_Content_btnSearch")
            search_btn.click()
            
            time.sleep(2)
            
            for page in range(1, max_pages + 1):
                # Parse current page
                rows = self.driver.find_elements(By.CSS_SELECTOR, "table.purchase-list tr[data-id]")
                
                for row in rows:
                    try:
                        procurement = {
                            "source": "sberbank-ast",
                            "procurement_number": row.find_element(By.CSS_SELECTOR, ".number").text,
                            "object_name": row.find_element(By.CSS_SELECTOR, ".name").text,
                            "customer_name": row.find_element(By.CSS_SELECTOR, ".customer").text,
                            "initial_price": self._parse_price(row.find_element(By.CSS_SELECTOR, ".price").text),
                            "published_date": row.find_element(By.CSS_SELECTOR, ".date").text,
                            "status": row.find_element(By.CSS_SELECTOR, ".status").text,
                            "collected_at": datetime.now().isoformat()
                        }
                        procurements.append(procurement)
                    except Exception as e:
                        logger.warning(f"Error parsing row: {e}")
                
                # Next page
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.next-page")
                    next_btn.click()
                    time.sleep(settings.commercial_delay_seconds)
                except NoSuchElementException:
                    break
            
            logger.info(f"Scraped {len(procurements)} from Sberbank-AST")
        
        except Exception as e:
            logger.error(f"Error scraping Sberbank-AST: {e}")
        
        return procurements
    
    def scrape_etpgpb(self, search_query: str = "Сбербанк") -> List[Dict]:
        """Scrape ETP GPB platform."""
        logger.info("Scraping ETP GPB...")
        procurements = []
        
        try:
            self.driver.get(self.PLATFORMS["etpgpb"]["url"])
            time.sleep(2)
            
            # Implement similar logic for ETP GPB
            # Structure varies per platform
            
            logger.info(f"Scraped {len(procurements)} from ETP GPB")
        
        except Exception as e:
            logger.error(f"Error scraping ETP GPB: {e}")
        
        return procurements
    
    def scrape_all_platforms(
        self,
        search_query: str = "Сбербанк",
        output_dir: str = "data/raw/commercial_etp"
    ) -> Dict[str, List[Dict]]:
        """Scrape all commercial platforms."""
        results = {}
        
        # Sberbank-AST
        results["sberbank-ast"] = self.scrape_sberbank_ast(search_query)
        
        # Save results
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for platform, data in results.items():
            output_file = Path(output_dir) / f"{platform}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data)} records to {output_file}")
        
        return results
    
    @staticmethod
    def _parse_price(price_str: str) -> Optional[float]:
        """Parse price string to float."""
        try:
            # Remove currency symbols and spaces
            price_str = price_str.replace("₽", "").replace(" ", "").replace(",", ".")
            return float(price_str)
        except:
            return None


def main():
    """Example usage."""
    with CommercialETPScraper(headless=True) as scraper:
        results = scraper.scrape_all_platforms(search_query="Сбербанк")
        print(f"Total platforms scraped: {len(results)}")
        for platform, data in results.items():
            print(f"  {platform}: {len(data)} procurements")


if __name__ == "__main__":
    main()
