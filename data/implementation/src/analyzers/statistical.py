"""Statistical analysis module."""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple
from src.utils.logger import logger

class StatisticalAnalyzer:
    """Perform statistical analysis on procurement data."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def descriptive_stats(self, columns: List[str] = None) -> pd.DataFrame:
        """
        Calculate descriptive statistics.
        
        Args:
            columns: Columns to analyze (default: all numeric)
        
        Returns:
            DataFrame with statistics
        """
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        stats_df = self.df[columns].describe()
        
        # Add additional metrics
        stats_df.loc['skew'] = self.df[columns].skew()
        stats_df.loc['kurtosis'] = self.df[columns].kurtosis()
        stats_df.loc['missing'] = self.df[columns].isnull().sum()
        stats_df.loc['missing_pct'] = (self.df[columns].isnull().sum() / len(self.df)) * 100
        
        logger.info(f"Calculated descriptive statistics for {len(columns)} columns")
        return stats_df
    
    def compare_groups(
        self,
        group_column: str,
        value_column: str,
        test: str = 'ttest'
    ) -> Dict:
        """
        Compare two groups using statistical tests.
        
        Args:
            group_column: Column with group labels
            value_column: Column with values to compare
            test: Test type ('ttest', 'mannwhitney', 'anova')
        
        Returns:
            Dictionary with test results
        """
        groups = self.df.groupby(group_column)[value_column].apply(list)
        
        if test == 'ttest' and len(groups) == 2:
            group1, group2 = groups.values
            statistic, pvalue = stats.ttest_ind(group1, group2, nan_policy='omit')
            
            result = {
                "test": "Independent t-test",
                "groups": groups.index.tolist(),
                "statistic": statistic,
                "p_value": pvalue,
                "significant": pvalue < 0.05
            }
        
        elif test == 'mannwhitney' and len(groups) == 2:
            group1, group2 = groups.values
            statistic, pvalue = stats.mannwhitneyu(group1, group2, alternative='two-sided')
            
            result = {
                "test": "Mann-Whitney U test",
                "groups": groups.index.tolist(),
                "statistic": statistic,
                "p_value": pvalue,
                "significant": pvalue < 0.05
            }
        
        elif test == 'anova':
            f_stat, pvalue = stats.f_oneway(*groups.values)
            
            result = {
                "test": "One-way ANOVA",
                "groups": groups.index.tolist(),
                "f_statistic": f_stat,
                "p_value": pvalue,
                "significant": pvalue < 0.05
            }
        
        else:
            raise ValueError(f"Unsupported test: {test}")
        
        logger.info(f"Performed {result['test']}: p={result['p_value']:.4f}")
        return result
    
    def time_series_analysis(
        self,
        date_column: str,
        value_column: str,
        freq: str = 'M'
    ) -> pd.DataFrame:
        """
        Analyze time series data.
        
        Args:
            date_column: Date column
            value_column: Value column to aggregate
            freq: Frequency ('D', 'W', 'M', 'Q', 'Y')
        
        Returns:
            DataFrame with time series statistics
        """
        df_ts = self.df.copy()
        df_ts[date_column] = pd.to_datetime(df_ts[date_column])
        df_ts = df_ts.set_index(date_column)
        
        # Resample by frequency
        ts_agg = df_ts[value_column].resample(freq).agg([
            ('count', 'count'),
            ('sum', 'sum'),
            ('mean', 'mean'),
            ('median', 'median'),
            ('std', 'std'),
            ('min', 'min'),
            ('max', 'max')
        ])
        
        # Calculate growth rates
        ts_agg['growth_rate'] = ts_agg['sum'].pct_change() * 100
        ts_agg['cumulative_sum'] = ts_agg['sum'].cumsum()
        
        logger.info(f"Time series analysis: {len(ts_agg)} periods")
        return ts_agg
    
    def calculate_savings_metrics(self) -> Dict:
        """
        Calculate procurement savings metrics.
        
        Returns:
            Dictionary with savings statistics
        """
        if 'initial_price' not in self.df.columns or 'contract_price' not in self.df.columns:
            logger.warning("Price columns not found")
            return {}
        
        df_complete = self.df[
            self.df['initial_price'].notna() &
            self.df['contract_price'].notna() &
            (self.df['initial_price'] > 0)
        ].copy()
        
        # Calculate savings
        df_complete['savings_amount'] = df_complete['initial_price'] - df_complete['contract_price']
        df_complete['savings_percent'] = (df_complete['savings_amount'] / df_complete['initial_price']) * 100
        
        metrics = {
            "total_procurements": len(df_complete),
            "total_nmck": df_complete['initial_price'].sum(),
            "total_contracts": df_complete['contract_price'].sum(),
            "total_savings": df_complete['savings_amount'].sum(),
            "avg_savings_percent": df_complete['savings_percent'].mean(),
            "median_savings_percent": df_complete['savings_percent'].median(),
            "procurements_with_savings": len(df_complete[df_complete['savings_amount'] > 0]),
            "procurements_with_overspend": len(df_complete[df_complete['savings_amount'] < 0]),
            "max_savings_percent": df_complete['savings_percent'].max(),
            "min_savings_percent": df_complete['savings_percent'].min()
        }
        
        logger.info(f"Savings metrics: avg={metrics['avg_savings_percent']:.2f}%")
        return metrics
    
    def competition_analysis(self) -> Dict:
        """
        Analyze competition level in procurements.
        
        Returns:
            Dictionary with competition statistics
        """
        if 'participants_count' not in self.df.columns:
            logger.warning("Participants count column not found")
            return {}
        
        df_comp = self.df[self.df['participants_count'].notna()].copy()
        
        metrics = {
            "total_procurements": len(df_comp),
            "avg_participants": df_comp['participants_count'].mean(),
            "median_participants": df_comp['participants_count'].median(),
            "monopoly_count": len(df_comp[df_comp['participants_count'] == 1]),
            "monopoly_percent": (len(df_comp[df_comp['participants_count'] == 1]) / len(df_comp)) * 100,
            "competitive_count": len(df_comp[df_comp['participants_count'] > 1]),
            "competitive_percent": (len(df_comp[df_comp['participants_count'] > 1]) / len(df_comp)) * 100,
            "max_participants": int(df_comp['participants_count'].max())
        }
        
        # Compare savings by competition level
        monopoly_savings = df_comp[df_comp['participants_count'] == 1]['savings_percent'].mean()
        competitive_savings = df_comp[df_comp['participants_count'] > 1]['savings_percent'].mean()
        
        metrics['monopoly_avg_savings'] = monopoly_savings
        metrics['competitive_avg_savings'] = competitive_savings
        metrics['savings_difference'] = competitive_savings - monopoly_savings
        
        logger.info(f"Competition: {metrics['monopoly_percent']:.1f}% monopoly, {metrics['competitive_percent']:.1f}% competitive")
        return metrics
    
    def distribution_analysis(
        self,
        column: str,
        bins: int = 50
    ) -> Dict:
        """
        Analyze distribution of values.
        
        Args:
            column: Column to analyze
            bins: Number of bins for histogram
        
        Returns:
            Dictionary with distribution metrics
        """
        data = self.df[column].dropna()
        
        # Basic metrics
        metrics = {
            "count": len(data),
            "mean": data.mean(),
            "median": data.median(),
            "std": data.std(),
            "skewness": stats.skew(data),
            "kurtosis": stats.kurtosis(data)
        }
        
        # Quartiles
        q1, q2, q3 = data.quantile([0.25, 0.5, 0.75])
        metrics['q1'] = q1
        metrics['q2'] = q2
        metrics['q3'] = q3
        metrics['iqr'] = q3 - q1
        
        # Test for normality
        if len(data) >= 3:
            _, p_value = stats.shapiro(data[:5000])  # Limit for performance
            metrics['normality_test_pvalue'] = p_value
            metrics['is_normal'] = p_value > 0.05
        
        logger.info(f"Distribution analysis for {column}: mean={metrics['mean']:.2f}, skew={metrics['skewness']:.2f}")
        return metrics


def main():
    """Example usage."""
    # Create sample data
    np.random.seed(42)
    data = {
        'procurement_id': range(1000),
        'published_date': pd.date_range('2024-01-01', periods=1000, freq='D'),
        'initial_price': np.random.lognormal(15, 1, 1000),
        'contract_price': np.random.lognormal(15, 1, 1000) * 0.9,
        'participants_count': np.random.choice([1, 2, 3, 4, 5], 1000, p=[0.2, 0.3, 0.25, 0.15, 0.1]),
        'category': np.random.choice(['IT', 'Construction', 'Services'], 1000)
    }
    df = pd.DataFrame(data)
    
    analyzer = StatisticalAnalyzer(df)
    
    # Descriptive stats
    print("Descriptive Statistics:")
    print(analyzer.descriptive_stats(['initial_price', 'contract_price']))
    
    # Savings metrics
    print("\nSavings Metrics:")
    print(analyzer.calculate_savings_metrics())
    
    # Competition analysis
    print("\nCompetition Analysis:")
    print(analyzer.competition_analysis())


if __name__ == "__main__":
    main()
