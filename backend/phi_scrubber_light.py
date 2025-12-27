"""
Lightweight PHI (Personal Health Information) Scrubber
Uses regex patterns instead of heavy spacy models
Suitable for resource-constrained environments
"""

import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class LightweightPHIScrubber:
    """
    Simple regex-based PHI detection and redaction
    Replaces heavy spacy model (250MB) with lightweight patterns
    """
    
    # PHI patterns
    PATTERNS = {
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",  # Social Security Number
        "PHONE": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",  # 4 groups of 4 digits
        "MRN": r"\bMRN\s*[:=]?\s*(\w+)\b",  # Medical Record Number
        "PATIENT_ID": r"\bPID\s*[:=]?\s*(\w+)\b",
        "DATE": r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/]\d{2,4}\b",
        "ZIP": r"\b\d{5}(?:-\d{4})?\b",  # ZIP code
    }
    
    REPLACEMENTS = {
        "SSN": "[SSN]",
        "PHONE": "[PHONE]",
        "EMAIL": "[EMAIL]",
        "CREDIT_CARD": "[CREDIT_CARD]",
        "MRN": "[MRN]",
        "PATIENT_ID": "[PATIENT_ID]",
        "DATE": "[DATE]",
        "ZIP": "[ZIP]",
    }
    
    @classmethod
    def scrub(cls, text: str) -> str:
        """
        Scrub PHI from text using regex patterns
        Returns text with PHI replaced by placeholders
        """
        if not text:
            return text
        
        scrubbed = text
        detected = []
        
        for phi_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, scrubbed, re.IGNORECASE)
            if matches:
                detected.append(phi_type)
                scrubbed = re.sub(
                    pattern,
                    cls.REPLACEMENTS[phi_type],
                    scrubbed,
                    flags=re.IGNORECASE
                )
        
        if detected:
            logger.debug(f"Detected and scrubbed PHI types: {', '.join(detected)}")
        
        return scrubbed
    
    @classmethod
    def analyze(cls, text: str) -> Dict[str, List[str]]:
        """
        Analyze text and return detected PHI types and values
        """
        if not text:
            return {}
        
        findings = {}
        
        for phi_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Flatten if tuple (regex groups)
                if isinstance(matches[0], tuple):
                    matches = [''.join(m) if isinstance(m, tuple) else m for m in matches]
                findings[phi_type] = list(set(matches))  # Remove duplicates
        
        return findings
    
    @classmethod
    def scrub_with_analysis(cls, text: str) -> Tuple[str, Dict[str, List[str]]]:
        """
        Scrub text and return both scrubbed text and detected PHI
        """
        analysis = cls.analyze(text)
        scrubbed = cls.scrub(text)
        return scrubbed, analysis


# For backward compatibility
class PHIScrubber:
    """Alias for lightweight scrubber"""
    
    @staticmethod
    def scrub(text: str) -> str:
        return LightweightPHIScrubber.scrub(text)
    
    @staticmethod
    def analyze(text: str) -> Dict[str, List[str]]:
        return LightweightPHIScrubber.analyze(text)
