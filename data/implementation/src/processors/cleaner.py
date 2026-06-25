"""Data cleaning and deduplication module."""
import pandas as pd
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from src.utils.logger import logger

class DataCleaner:
    """Clean and deduplicate procurement data."""
    
    # Source priority (higher = more reliable)
    SOURCE_PRIORITY = {
        "eis": 10,
        "sberbank-ast": 8,
        "etpgpb": 7,
        "rts-tender": 6,
        "roseltorg": 5,
        "lot-online": 4,
        "other": 1
    }
    
    def __init__(self):
        self.duplicate_stats = {
            "exact": 0,
            "fuzzy": 0,
            "by_number": 0
        }
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame with basic operations.
        
        Args:
            df: Input DataFrame
        
        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()
        
        # Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Strip whitespace from string columns
        string_cols = df_clean.select_dtypes(include=['object']).columns
        for col in string_cols:
            df_clean[col] = df_clean[col].str.strip() if df_clean[col].dtype == 'object' else df_clean[col]
        
        # Standardize dates
        date_cols = ['published_date', 'contract_date', 'submission_deadline']
        for col in date_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        
        # Standardize prices
        price_cols = ['initial_price', 'contract_price']
        for col in price_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        logger.info(f"Cleaned DataFrame: {len(df)} -> {len(df_clean)} rows")
        return df_clean
    
    def remove_exact_duplicates(
        self,
        df: pd.DataFrame,
        subset: List[str] = None
    ) -> pd.DataFrame:
        """
        Remove exact duplicates.
        
        Args:
            df: Input DataFrame
            subset: Columns to consider for duplicate detection
        
        Returns:
            DataFrame without exact duplicates
        """
        if subset is None:
            subset = ['procurement_number']
        
        initial_count = len(df)
        df_dedup = df.drop_duplicates(subset=subset, keep='first')
        
        self.duplicate_stats["exact"] = initial_count - len(df_dedup)
        logger.info(f"Removed {self.duplicate_stats['exact']} exact duplicates")
        
        return df_dedup
    
    def remove_duplicates_by_priority(
        self,
        df: pd.DataFrame,
        key_columns: List[str] = ['customer_inn', 'published_date', 'initial_price']
    ) -> pd.DataFrame:
        """
        Remove duplicates keeping records from higher priority sources.
        
        Args:
            df: Input DataFrame
            key_columns: Columns defining a unique procurement
        
        Returns:
            DataFrame with duplicates removed by priority
        """
        # Add source priority
        df['_priority'] = df['source'].map(self.SOURCE_PRIORITY).fillna(1)
        
        # Sort by priority (descending) and drop duplicates
        df_sorted = df.sort_values('_priority', ascending=False)
        initial_count = len(df_sorted)
        df_dedup = df_sorted.drop_duplicates(subset=key_columns, keep='first')
        
        # Remove temporary column
        df_dedup = df_dedup.drop('_priority', axis=1)
        
        removed = initial_count - len(df_dedup)
        self.duplicate_stats["by_number"] = removed
        logger.info(f"Removed {removed} duplicates by source priority")
        
        return df_dedup
    
    def find_fuzzy_duplicates(
        self,
        df: pd.DataFrame,
        text_column: str = 'object_description',
        threshold: float = 0.95,
        max_comparisons: int = 10000
    ) -> List[Tuple[int, int, float]]:
        """
        Find fuzzy duplicates based on text similarity.
        
        Args:
            df: Input DataFrame
            text_column: Column to compare
            threshold: Similarity threshold (0-1)
            max_comparisons: Maximum comparisons to perform
        
        Returns:
            List of (index1, index2, similarity) tuples
        """
        fuzzy_duplicates = []
        
        # Limit comparisons for performance
        df_sample = df.head(min(len(df), max_comparisons))
        
        for i, row1 in df_sample.iterrows():
            if not isinstance(row1[text_column], str):
                continue
            
            for j, row2 in df_sample.iterrows():
                if i >= j or not isinstance(row2[text_column], str):
                    continue
                
                similarity = SequenceMatcher(
                    None,
                    row1[text_column],
                    row2[text_column]
                ).ratio()
                
                if similarity >= threshold:
                    fuzzy_duplicates.append((i, j, similarity))
        
        self.duplicate_stats["fuzzy"] = len(fuzzy_duplicates)
        logger.info(f"Found {len(fuzzy_duplicates)} fuzzy duplicates")
        
        return fuzzy_duplicates
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data and add quality score.
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame with data_quality_score column
        """
        df_valid = df.copy()
        
        # Required fields
        required_fields = [
            'procurement_number',
            'customer_id',
            'initial_price',
            'published_date'
        ]
        
        # Calculate completeness score
        def calculate_quality_score(row):
            score = 0.0
            total_fields = len(required_fields)
            
            for field in required_fields:
                if field in row and pd.notna(row[field]) and row[field] != '':
                    score += 1.0
            
            return score / total_fields if total_fields > 0 else 0.0
        
        df_valid['data_quality_score'] = df_valid.apply(calculate_quality_score, axis=1)
        
        # Log quality statistics
        avg_quality = df_valid['data_quality_score'].mean()
        low_quality = len(df_valid[df_valid['data_quality_score'] < 0.5])
        
        logger.info(f"Average data quality score: {avg_quality:.2f}")
        logger.info(f"Records with low quality (<0.5): {low_quality}")
        
        return df_valid
    
    def get_duplicate_report(self) -> Dict:
        """Get duplicate statistics report."""
        return {
            "total_duplicates": sum(self.duplicate_stats.values()),
            **self.duplicate_stats
        }


def main():
    """Example usage."""
    # Create sample data with duplicates
    data = {
        'procurement_number': ['001', '001', '002', '003', '003'],
        'source': ['eis', 'sberbank-ast', 'eis', 'eis', 'etpgpb'],
        'customer_inn': ['1234', '1234', '5678', '9012', '9012'],
        'initial_price': [1000000, 1000000, 2000000, 500000, 500000],
        'published_date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-03', '2024-01-03'],
        'object_description': ['Test', 'Test', 'Another', 'Third', 'Third']
    }
    
    df = pd.DataFrame(data)
    print(f"Original: {len(df)} rows")
    
    cleaner = DataCleaner()
    
    # Clean
    df_clean = cleaner.clean_dataframe(df)
    
    # Remove duplicates
    df_dedup = cleaner.remove_exact_duplicates(df_clean)
    print(f"After exact dedup: {len(df_dedup)} rows")
    
    df_final = cleaner.remove_duplicates_by_priority(df_dedup)
    print(f"After priority dedup: {len(df_final)} rows")
    
    # Report
    print("\nDuplicate Report:")
    print(cleaner.get_duplicate_report())


if __name__ == "__main__":
    main()
