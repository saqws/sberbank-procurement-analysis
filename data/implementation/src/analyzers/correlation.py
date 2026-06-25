"""Correlation analysis with external factors."""
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from typing import Dict, List, Tuple
from src.utils.logger import logger

class CorrelationAnalyzer:
    """Analyze correlations between procurement data and external factors."""
    
    def __init__(self, df_proc: pd.DataFrame, df_external: pd.DataFrame = None):
        self.df_proc = df_proc
        self.df_external = df_external
    
    def calculate_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series,
        method: str = 'pearson',
        lag: int = 0
    ) -> Tuple[float, float]:
        """Calculate correlation between two series."""
        if lag > 0:
            series2 = series2.shift(lag)
        
        # Remove NaN values
        mask = series1.notna() & series2.notna()
        s1 = series1[mask]
        s2 = series2[mask]
        
        if len(s1) < 3:
            return 0.0, 1.0
        
        if method == 'pearson':
            corr, pval = pearsonr(s1, s2)
        elif method == 'spearman':
            corr, pval = spearmanr(s1, s2)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return corr, pval
    
    def correlate_with_usd(
        self,
        df_usd: pd.DataFrame,
        category: str = None,
        max_lag: int = 6
    ) -> Dict:
        """Correlate procurement volumes with USD rate."""
        # Aggregate by month
        df_monthly = self.df_proc.copy()
        df_monthly['month'] = pd.to_datetime(df_monthly['published_date']).dt.to_period('M')
        
        if category:
            df_monthly = df_monthly[df_monthly['category'] == category]
        
        monthly_volume = df_monthly.groupby('month')['contract_price'].sum()
        
        # Merge with USD rates
        df_usd['month'] = pd.to_datetime(df_usd['date']).dt.to_period('M')
        usd_monthly = df_usd.groupby('month')['rate'].mean()
        
        # Test different lags
        results = []
        for lag in range(max_lag + 1):
            corr, pval = self.calculate_correlation(monthly_volume, usd_monthly, lag=lag)
            results.append({
                'lag': lag,
                'correlation': corr,
                'p_value': pval,
                'significant': pval < 0.05
            })
        
        best = max(results, key=lambda x: abs(x['correlation']))
        logger.info(f"Best USD correlation: {best['correlation']:.3f} at lag {best['lag']}")
        
        return {
            'category': category or 'all',
            'best_lag': best['lag'],
            'best_correlation': best['correlation'],
            'p_value': best['p_value'],
            'all_lags': results
        }
    
    def correlate_with_key_rate(self, df_key_rate: pd.DataFrame) -> Dict:
        """Correlate with CBR key rate."""
        df_monthly = self.df_proc.copy()
        df_monthly['month'] = pd.to_datetime(df_monthly['published_date']).dt.to_period('M')
        monthly_volume = df_monthly.groupby('month')['contract_price'].sum()
        
        df_key_rate['month'] = pd.to_datetime(df_key_rate['date']).dt.to_period('M')
        key_rate_monthly = df_key_rate.groupby('month')['rate'].mean()
        
        corr, pval = self.calculate_correlation(monthly_volume, key_rate_monthly)
        
        logger.info(f"Key rate correlation: {corr:.3f} (p={pval:.4f})")
        return {
            'correlation': corr,
            'p_value': pval,
            'significant': pval < 0.05
        }
    
    def correlation_matrix(self, columns: List[str]) -> pd.DataFrame:
        """Calculate correlation matrix."""
        return self.df_proc[columns].corr()


def main():
    """Example."""
    np.random.seed(42)
    df_proc = pd.DataFrame({
        'published_date': pd.date_range('2024-01-01', periods=365, freq='D'),
        'contract_price': np.random.lognormal(15, 1, 365),
        'category': np.random.choice(['IT', 'Construction'], 365)
    })
    
    df_usd = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=365, freq='D'),
        'rate': 90 + np.cumsum(np.random.randn(365) * 0.5)
    })
    
    analyzer = CorrelationAnalyzer(df_proc)
    result = analyzer.correlate_with_usd(df_usd, category='IT')
    print(f"IT-USD correlation: {result['best_correlation']:.3f}")


if __name__ == "__main__":
    main()
