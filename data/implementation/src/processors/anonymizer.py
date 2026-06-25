"""Personal data anonymization module."""
import re
import hashlib
from typing import Optional, Dict, List
from src.utils.logger import logger

class Anonymizer:
    """Anonymize personal data in text."""
    
    # Patterns for different types of PD
    PATTERNS = {
        "fio": [
            # Иванов Иван Иванович
            r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b',
            # И.И. Иванов
            r'\b[А-ЯЁ]\.[А-ЯЁ]\.\s+[А-ЯЁ][а-яё]+\b',
            # Иванов И.И.
            r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.\b'
        ],
        "passport": [
            # 1234 567890
            r'\b\d{4}\s*\d{6}\b',
            # паспорт серии 1234 номер 567890
            r'(?:паспорт|серии|серия|номер)[\s:]+\d{4}[\s:]+\d{6}\b'
        ],
        "snils": [
            # 123-456-789 01
            r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}\b'
        ],
        "inn_physical": [
            # 12-digit INN (физлица)
            r'\b\d{12}\b'
        ],
        "phone": [
            # +7 (123) 456-78-90
            r'\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b',
            # 8-123-456-78-90
            r'\b8[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b'
        ],
        "email": [
            # Standard email pattern
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]
    }
    
    # Replacement templates
    REPLACEMENTS = {
        "fio": "[ФИО]",
        "passport": "[ПАСПОРТ]",
        "snils": "[СНИЛС]",
        "inn_physical": "[ИНН]",
        "phone": "[ТЕЛЕФОН]",
        "email": "[EMAIL]"
    }
    
    def __init__(self, use_hashing: bool = False):
        """
        Initialize anonymizer.
        
        Args:
            use_hashing: If True, replace with hash instead of template
        """
        self.use_hashing = use_hashing
        self.hash_cache = {}
    
    def _hash_value(self, value: str, pd_type: str) -> str:
        """Generate consistent hash for value."""
        if value in self.hash_cache:
            return self.hash_cache[value]
        
        hash_obj = hashlib.sha256(value.encode())
        hash_hex = hash_obj.hexdigest()[:16]
        hashed = f"[{pd_type.upper()}_{hash_hex}]"
        
        self.hash_cache[value] = hashed
        return hashed
    
    def anonymize_text(self, text: str, preserve_structure: bool = True) -> str:
        """
        Anonymize all personal data in text.
        
        Args:
            text: Input text
            preserve_structure: If True, maintain text structure
        
        Returns:
            Anonymized text
        """
        if not text:
            return text
        
        result = text
        pd_found = []
        
        # Process each PD type
        for pd_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, result, re.IGNORECASE)
                
                for match in matches:
                    original = match.group(0)
                    
                    if self.use_hashing:
                        replacement = self._hash_value(original, pd_type)
                    else:
                        replacement = self.REPLACEMENTS[pd_type]
                    
                    result = result.replace(original, replacement)
                    pd_found.append((pd_type, original))
        
        if pd_found:
            logger.debug(f"Anonymized {len(pd_found)} PD items: {[t for t, _ in pd_found]}")
        
        return result
    
    def anonymize_dict(self, data: Dict, text_fields: List[str]) -> Dict:
        """
        Anonymize specific fields in dictionary.
        
        Args:
            data: Input dictionary
            text_fields: List of field names to anonymize
        
        Returns:
            Dictionary with anonymized fields
        """
        result = data.copy()
        
        for field in text_fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.anonymize_text(result[field])
        
        return result
    
    def anonymize_dataframe(self, df, text_columns: List[str]):
        """
        Anonymize specific columns in pandas DataFrame.
        
        Args:
            df: Input DataFrame
            text_columns: List of column names to anonymize
        
        Returns:
            DataFrame with anonymized columns
        """
        df_copy = df.copy()
        
        for col in text_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].apply(
                    lambda x: self.anonymize_text(x) if isinstance(x, str) else x
                )
                logger.info(f"Anonymized column: {col}")
        
        return df_copy
    
    def detect_pd(self, text: str) -> Dict[str, List[str]]:
        """
        Detect personal data without anonymization.
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with PD types and found values
        """
        result = {}
        
        for pd_type, patterns in self.PATTERNS.items():
            found = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                found.extend(matches)
            
            if found:
                result[pd_type] = list(set(found))
        
        return result
    
    def validate_anonymization(self, original: str, anonymized: str) -> bool:
        """
        Validate that anonymization removed all PD.
        
        Args:
            original: Original text
            anonymized: Anonymized text
        
        Returns:
            True if no PD found in anonymized text
        """
        pd_in_anonymized = self.detect_pd(anonymized)
        
        if pd_in_anonymized:
            logger.warning(f"PD still present after anonymization: {list(pd_in_anonymized.keys())}")
            return False
        
        return True


def main():
    """Example usage."""
    anonymizer = Anonymizer(use_hashing=True)
    
    # Test text
    text = """
    Контактное лицо: Иванов Иван Иванович
    Паспорт: 1234 567890
    СНИЛС: 123-456-789-01
    Телефон: +7 (495) 123-45-67
    Email: ivanov@example.com
    ИНН: 123456789012
    """
    
    print("Original:")
    print(text)
    print("\nAnonymized:")
    print(anonymizer.anonymize_text(text))
    
    # Detection
    pd_found = anonymizer.detect_pd(text)
    print("\nDetected PD:")
    for pd_type, values in pd_found.items():
        print(f"  {pd_type}: {len(values)} items")


if __name__ == "__main__":
    main()
