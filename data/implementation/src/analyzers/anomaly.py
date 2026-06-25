"""Anomaly detection module."""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Dict
from src.utils.logger import logger

class AnomalyDetector:
    """Detect anomalies in procurement data."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.anomalies = []
    
    def detect_by_iqr(self, column: str, multiplier: float = 1.5) -> pd.Series:
        """Detect outliers using IQR method."""
        Q1 = self.df[column].quantile(0.25)
        Q3 = self.df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR
        
        is_anomaly = (self.df[column] < lower) | (self.df[column] > upper)
        logger.info(f"IQR: {is_anomaly.sum()} anomalies in {column}")
        return is_anomaly
    
    def detect_by_zscore(self, column: str, threshold: float = 3) -> pd.Series:
        """Detect outliers using Z-score."""
        z_scores = np.abs((self.df[column] - self.df[column].mean()) / self.df[column].std())
        is_anomaly = z_scores > threshold
        logger.info(f"Z-score: {is_anomaly.sum()} anomalies in {column}")
        return is_anomaly
    
    def detect_by_isolation_forest(
        self,
        features: List[str],
        contamination: float = 0.05
    ) -> pd.Series:
        """Detect anomalies using Isolation Forest."""
        df_features = self.df[features].dropna()
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_features)
        
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        predictions = iso_forest.fit_predict(X_scaled)
        
        is_anomaly = pd.Series(predictions == -1, index=df_features.index)
        logger.info(f"Isolation Forest: {is_anomaly.sum()} anomalies")
        return is_anomaly
    
    def detect_monopoly_anomalies(self) -> List[Dict]:
        """Detect suspicious monopoly procurements."""
        if 'participants_count' not in self.df.columns:
            return []
        
        monopoly = self.df[self.df['participants_count'] == 1].copy()
        monopoly = monopoly[monopoly['savings_percent'] < 2]  # Very low savings
        
        anomalies = []
        for _, row in monopoly.iterrows():
            anomalies.append({
                'procurement_id': row.get('procurement_id'),
                'type': 'monopoly_zero_savings',
                'severity': 'medium',
                'description': f"Single participant with {row.get('savings_percent', 0):.1f}% savings"
            })
        
        logger.info(f"Found {len(anomalies)} monopoly anomalies")
        return anomalies
    
    def detect_price_anomalies(self) -> List[Dict]:
        """Detect suspicious price patterns."""
        if 'savings_percent' not in self.df.columns:
            return []
        
        anomalies = []
        
        # Excessive savings (>50%)
        excessive = self.df[self.df['savings_percent'] > 50]
        for _, row in excessive.iterrows():
            anomalies.append({
                'procurement_id': row.get('procurement_id'),
                'type': 'excessive_savings',
                'severity': 'high',
                'description': f"Savings of {row['savings_percent']:.1f}% - possible NMCK manipulation"
            })
        
        # Overspend (>20%)
        overspend = self.df[self.df['savings_percent'] < -20]
        for _, row in overspend.iterrows():
            anomalies.append({
                'procurement_id': row.get('procurement_id'),
                'type': 'overspend',
                'severity': 'high',
                'description': f"Overspend of {abs(row['savings_percent']):.1f}%"
            })
        
        logger.info(f"Found {len(anomalies)} price anomalies")
        return anomalies
    
    def detect_supplier_anomalies(self) -> List[Dict]:
        """Detect suspicious supplier patterns."""
        if 'winner_id' not in self.df.columns:
            return []
        
        # Calculate win rates
        winner_stats = self.df.groupby('winner_id').agg({
            'procurement_id': 'count',
            'contract_price': 'sum'
        }).rename(columns={'procurement_id': 'wins'})
        
        total = len(self.df)
        winner_stats['win_rate'] = winner_stats['wins'] / total
        
        # Flag high win rates (>30%)
        high_win_rate = winner_stats[winner_stats['win_rate'] > 0.3]
        
        anomalies = []
        for winner_id, row in high_win_rate.iterrows():
            anomalies.append({
                'supplier_id': winner_id,
                'type': 'high_win_rate',
                'severity': 'medium',
                'description': f"Win rate of {row['win_rate']*100:.1f}% ({row['wins']} wins)"
            })
        
        logger.info(f"Found {len(anomalies)} supplier anomalies")
        return anomalies
    
    def detect_all_anomalies(self) -> pd.DataFrame:
        """Run all detection methods."""
        all_anomalies = []
        
        # Business rule anomalies
        all_anomalies.extend(self.detect_monopoly_anomalies())
        all_anomalies.extend(self.detect_price_anomalies())
        all_anomalies.extend(self.detect_supplier_anomalies())
        
        df_anomalies = pd.DataFrame(all_anomalies)
        logger.info(f"Total anomalies detected: {len(df_anomalies)}")
        
        return df_anomalies


def main():
    """Example."""
    np.random.seed(42)
    df = pd.DataFrame({
        'procurement_id': range(1000),
        'contract_price': np.random.lognormal(15, 1, 1000),
        'initial_price': np.random.lognormal(15, 1, 1000) * 1.1,
        'participants_count': np.random.choice([1, 2, 3], 1000),
        'winner_id': np.random.choice(range(100), 1000)
    })
    df['savings_percent'] = ((df['initial_price'] - df['contract_price']) / df['initial_price']) * 100
    
    detector = AnomalyDetector(df)
    anomalies = detector.detect_all_anomalies()
    print(f"Detected {len(anomalies)} anomalies")
    print(anomalies['type'].value_counts())


if __name__ == "__main__":
    main()
