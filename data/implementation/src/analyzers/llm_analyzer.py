"""LLM-based analysis module."""
from typing import Optional, Dict, List
from src.utils.config import settings
from src.utils.logger import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available")

class LLMAnalyzer:
    """Use LLM for analyzing unstructured procurement data."""
    
    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed")
        
        self.api_key = api_key or settings.openai_api_key
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def classify_description(self, description: str) -> Dict:
        """Classify procurement description into categories."""
        if not self.client:
            return {"category": "unknown", "confidence": 0.0}
        
        prompt = f"""Classify this procurement into one of these categories: IT, Construction, Services, Equipment, Consulting.
        
Description: {description[:500]}

Return only: Category"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )
            
            category = response.choices[0].message.content.strip()
            return {"category": category, "confidence": 1.0}
        
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            return {"category": "unknown", "confidence": 0.0}
    
    def extract_key_terms(self, description: str) -> List[str]:
        """Extract key terms from description."""
        if not self.client:
            return []
        
        prompt = f"""Extract 5-7 key terms from this procurement description.

Description: {description[:1000]}

Return as comma-separated list."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0
            )
            
            terms = response.choices[0].message.content.strip().split(',')
            return [t.strip() for t in terms]
        
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return []
    
    def analyze_anomaly(self, anomaly_data: Dict) -> str:
        """Generate explanation for anomaly."""
        if not self.client:
            return "LLM not available"
        
        prompt = f"""Analyze this procurement anomaly and provide a brief explanation:

Type: {anomaly_data.get('type')}
Severity: {anomaly_data.get('severity')}
Description: {anomaly_data.get('description')}

Provide 2-3 sentence analysis of possible causes and implications."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return "Analysis unavailable"
    
    def generate_insight(self, data_summary: str) -> str:
        """Generate analytical insight from data summary."""
        if not self.client:
            return "LLM not available"
        
        prompt = f"""Based on this procurement data summary, provide a professional analytical insight:

{data_summary}

Format:
Observation: [what the data shows]
Interpretation: [why this might be happening]
Significance: [why this matters]"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"LLM insight error: {e}")
            return "Insight generation unavailable"


def main():
    """Example."""
    analyzer = LLMAnalyzer()
    
    description = "Поставка серверного оборудования HPE ProLiant DL380 Gen10"
    result = analyzer.classify_description(description)
    print(f"Classification: {result}")
    
    terms = analyzer.extract_key_terms(description)
    print(f"Key terms: {terms}")


if __name__ == "__main__":
    main()
