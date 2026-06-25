"""Central Bank of Russia API client for exchange rates and key rate."""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from src.utils.logger import logger

class CBRClient:
    """Client for Central Bank of Russia API."""
    
    # Daily rates API
    DAILY_JSON_URL = "https://www.cbr-xml-daily.ru/archive/{date}/daily_json.js"
    
    # Key rate (manually maintained list - CBR doesn't have simple API)
    KEY_RATES = [
        {"date": "2024-01-01", "rate": 16.00},
        {"date": "2024-02-14", "rate": 16.00},
        {"date": "2024-03-22", "rate": 16.00},
        {"date": "2024-04-26", "rate": 16.00},
        {"date": "2024-06-07", "rate": 16.00},
        {"date": "2024-07-26", "rate": 18.00},
        {"date": "2024-09-13", "rate": 19.00},
        {"date": "2024-10-25", "rate": 21.00},
        {"date": "2024-12-20", "rate": 21.00},
        {"date": "2025-01-01", "rate": 21.00}
    ]
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_exchange_rate(self, date: str, currency: str = "USD") -> float:
        """
        Get exchange rate for specific date and currency.
        
        Args:
            date: Date in YYYY-MM-DD format
            currency: Currency code (USD, EUR, CNY, etc.)
        
        Returns:
            Exchange rate value
        """
        try:
            url = self.DAILY_JSON_URL.format(date=date.replace("-", "/"))
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Find currency in Valute dict
            if currency in data.get("Valute", {}):
                return data["Valute"][currency]["Value"]
            else:
                logger.warning(f"Currency {currency} not found for date {date}")
                return None
        
        except Exception as e:
            logger.error(f"Error fetching exchange rate for {date}: {e}")
            return None
    
    def get_exchange_rates_range(
        self,
        start_date: str,
        end_date: str,
        currencies: List[str] = ["USD", "EUR", "CNY"]
    ) -> pd.DataFrame:
        """
        Get exchange rates for date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            currencies: List of currency codes
        
        Returns:
            DataFrame with dates and exchange rates
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        date_range = pd.date_range(start, end, freq='D')
        
        data = []
        for date in date_range:
            date_str = date.strftime("%Y-%m-%d")
            row = {"date": date_str}
            
            for currency in currencies:
                rate = self.get_exchange_rate(date_str, currency)
                if rate:
                    row[f"{currency}_rate"] = rate
            
            if len(row) > 1:  # Has at least one rate
                data.append(row)
        
        df = pd.DataFrame(data)
        logger.info(f"Fetched exchange rates for {len(df)} days")
        return df
    
    def get_key_rate_range(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Get key rates for date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with dates and key rates
        """
        df = pd.DataFrame(self.KEY_RATES)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by date range
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        df = df[(df['date'] >= start) & (df['date'] <= end)]
        
        # Forward fill to get daily rates
        date_range = pd.date_range(start, end, freq='D')
        df_daily = pd.DataFrame({'date': date_range})
        df_daily = df_daily.merge(df, on='date', how='left')
        df_daily['rate'] = df_daily['rate'].fillna(method='ffill')
        
        logger.info(f"Fetched key rates for {len(df_daily)} days")
        return df_daily
    
    def save_to_db(self, df: pd.DataFrame, table_name: str):
        """Save data to database."""
        from src.utils.db import engine
        df.to_sql(table_name, engine, if_exists='append', index=False)
        logger.info(f"Saved {len(df)} records to {table_name}")


def main():
    """Example usage."""
    client = CBRClient()
    
    # Exchange rates
    df_rates = client.get_exchange_rates_range(
        start_date="2024-01-01",
        end_date="2024-01-31",
        currencies=["USD", "EUR", "CNY"]
    )
    print(df_rates.head())
    
    # Key rate
    df_key_rate = client.get_key_rate_range(
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    print(df_key_rate.head())


if __name__ == "__main__":
    main()
