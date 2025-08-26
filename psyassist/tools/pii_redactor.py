"""
PII (Personally Identifiable Information) redactor for PsyAssist AI.
"""

import re
import hashlib
from typing import Dict, List, Tuple, Any
from datetime import datetime
from abc import ABC, abstractmethod


class BasePIIRedactor(ABC):
    """Abstract base class for PII redactors."""
    
    @abstractmethod
    def redact_text(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Redact PII from text and return redacted text with metadata."""
        pass
    
    @abstractmethod
    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Redact PII from dictionary and return redacted data with metadata."""
        pass


class RegexPIIRedactor(BasePIIRedactor):
    """Regex-based PII redactor implementation."""
    
    def __init__(self):
        self._build_patterns()
    
    def _build_patterns(self):
        """Build regex patterns for PII detection."""
        self.patterns = {
            # Phone numbers
            'phone': re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'),
            
            # Email addresses
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            
            # Social Security Numbers (US)
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            
            # Credit card numbers
            'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
            
            # IP addresses
            'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            
            # Names (basic patterns)
            'name': re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),
            
            # Addresses (basic patterns)
            'address': re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b'),
            
            # Dates (various formats)
            'date': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b'),
            
            # ZIP codes (US)
            'zip_code': re.compile(r'\b\d{5}(?:-\d{4})?\b'),
        }
        
        # Replacement patterns
        self.replacements = {
            'phone': '[PHONE]',
            'email': '[EMAIL]',
            'ssn': '[SSN]',
            'credit_card': '[CREDIT_CARD]',
            'ip_address': '[IP_ADDRESS]',
            'name': '[NAME]',
            'address': '[ADDRESS]',
            'date': '[DATE]',
            'zip_code': '[ZIP_CODE]',
        }
    
    def redact_text(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Redact PII from text."""
        redacted_text = text
        redaction_metadata = {
            'redactions': [],
            'total_redactions': 0,
            'redaction_types': set(),
            'original_length': len(text),
            'redacted_length': len(text)
        }
        
        for pii_type, pattern in self.patterns.items():
            matches = list(pattern.finditer(text))
            
            for match in matches:
                original_value = match.group()
                replacement = self.replacements[pii_type]
                
                # Create hash of original value for potential recovery
                value_hash = hashlib.sha256(original_value.encode()).hexdigest()[:8]
                
                redaction_info = {
                    'type': pii_type,
                    'start': match.start(),
                    'end': match.end(),
                    'original_value': original_value,
                    'replacement': replacement,
                    'hash': value_hash
                }
                
                redaction_metadata['redactions'].append(redaction_info)
                redaction_metadata['redaction_types'].add(pii_type)
        
        # Sort redactions by start position (reverse order to maintain indices)
        redaction_metadata['redactions'].sort(key=lambda x: x['start'], reverse=True)
        
        # Apply redactions
        for redaction in redaction_metadata['redactions']:
            start = redaction['start']
            end = redaction['end']
            replacement = redaction['replacement']
            
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
        
        redaction_metadata['total_redactions'] = len(redaction_metadata['redactions'])
        redaction_metadata['redaction_types'] = list(redaction_metadata['redaction_types'])
        redaction_metadata['redacted_length'] = len(redacted_text)
        
        return redacted_text, redaction_metadata
    
    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Redact PII from dictionary recursively."""
        redacted_data = {}
        redaction_metadata = {
            'redactions': [],
            'total_redactions': 0,
            'redaction_types': set(),
            'redacted_fields': []
        }
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted_value, value_metadata = self.redact_text(value)
                redacted_data[key] = redacted_value
                
                if value_metadata['total_redactions'] > 0:
                    redaction_metadata['redactions'].extend(value_metadata['redactions'])
                    redaction_metadata['redaction_types'].update(value_metadata['redaction_types'])
                    redaction_metadata['redacted_fields'].append(key)
            
            elif isinstance(value, dict):
                redacted_value, value_metadata = self.redact_dict(value)
                redacted_data[key] = redacted_value
                
                redaction_metadata['redactions'].extend(value_metadata['redactions'])
                redaction_metadata['redaction_types'].update(value_metadata['redaction_types'])
                redaction_metadata['redacted_fields'].extend(value_metadata['redacted_fields'])
            
            elif isinstance(value, list):
                redacted_list = []
                for item in value:
                    if isinstance(item, str):
                        redacted_item, item_metadata = self.redact_text(item)
                        redacted_list.append(redacted_item)
                        
                        redaction_metadata['redactions'].extend(item_metadata['redactions'])
                        redaction_metadata['redaction_types'].update(item_metadata['redaction_types'])
                    
                    elif isinstance(item, dict):
                        redacted_item, item_metadata = self.redact_dict(item)
                        redacted_list.append(redacted_item)
                        
                        redaction_metadata['redactions'].extend(item_metadata['redactions'])
                        redaction_metadata['redaction_types'].update(item_metadata['redaction_types'])
                    
                    else:
                        redacted_list.append(item)
                
                redacted_data[key] = redacted_list
                
                if any(isinstance(item, (str, dict)) for item in value):
                    redaction_metadata['redacted_fields'].append(key)
            
            else:
                redacted_data[key] = value
        
        redaction_metadata['total_redactions'] = len(redaction_metadata['redactions'])
        redaction_metadata['redaction_types'] = list(redaction_metadata['redaction_types'])
        
        return redacted_data, redaction_metadata
    
    def is_pii_present(self, text: str) -> bool:
        """Check if PII is present in text."""
        for pattern in self.patterns.values():
            if pattern.search(text):
                return True
        return False
    
    def get_pii_types(self, text: str) -> List[str]:
        """Get types of PII present in text."""
        pii_types = []
        for pii_type, pattern in self.patterns.items():
            if pattern.search(text):
                pii_types.append(pii_type)
        return pii_types


class CustomPIIRedactor(RegexPIIRedactor):
    """Custom PII redactor with additional patterns for mental health context."""
    
    def __init__(self):
        super().__init__()
        self._add_mental_health_patterns()
    
    def _add_mental_health_patterns(self):
        """Add patterns specific to mental health context."""
        mental_health_patterns = {
            # Medication names (common ones)
            'medication': re.compile(r'\b(?:Prozac|Zoloft|Lexapro|Celexa|Paxil|Wellbutrin|Effexor|Cymbalta|Abilify|Risperdal|Seroquel|Zyprexa|Depakote|Lithium|Xanax|Ativan|Klonopin|Valium|Adderall|Ritalin|Vyvanse)\b', re.IGNORECASE),
            
            # Diagnosis terms (be careful with these)
            'diagnosis': re.compile(r'\b(?:depression|anxiety|bipolar|PTSD|OCD|ADHD|autism|schizophrenia|borderline|narcissistic|antisocial|dependent|avoidant|paranoid|schizoid|histrionic|obsessive|compulsive)\b', re.IGNORECASE),
            
            # Hospital/clinic names (basic pattern)
            'healthcare_facility': re.compile(r'\b(?:Hospital|Clinic|Medical Center|Health Center|Mental Health|Psychiatric|Behavioral Health)\b'),
            
            # Insurance information
            'insurance': re.compile(r'\b[A-Z]{2,3}\d{6,10}\b'),
            
            # Medical record numbers
            'medical_record': re.compile(r'\bMRN[:\s]*\d{6,10}\b'),
        }
        
        self.patterns.update(mental_health_patterns)
        
        # Add replacements for new patterns
        new_replacements = {
            'medication': '[MEDICATION]',
            'diagnosis': '[DIAGNOSIS]',
            'healthcare_facility': '[HEALTHCARE_FACILITY]',
            'insurance': '[INSURANCE]',
            'medical_record': '[MEDICAL_RECORD]',
        }
        
        self.replacements.update(new_replacements)


class PIIRedactor:
    """Main PII redactor interface."""
    
    def __init__(self, redactor_type: str = "custom"):
        self.redactor_type = redactor_type
        
        if redactor_type == "basic":
            self.redactor = RegexPIIRedactor()
        elif redactor_type == "custom":
            self.redactor = CustomPIIRedactor()
        else:
            raise ValueError(f"Unknown redactor type: {redactor_type}")
    
    def redact_text(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Redact PII from text."""
        return self.redactor.redact_text(text)
    
    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Redact PII from dictionary."""
        return self.redactor.redact_dict(data)
    
    def is_pii_present(self, text: str) -> bool:
        """Check if PII is present in text."""
        return self.redactor.is_pii_present(text)
    
    def get_pii_types(self, text: str) -> List[str]:
        """Get types of PII present in text."""
        return self.redactor.get_pii_types(text)
    
    def redact_for_logging(self, data: Any) -> Any:
        """Redact data specifically for logging purposes."""
        if isinstance(data, str):
            redacted_text, _ = self.redact_text(data)
            return redacted_text
        elif isinstance(data, dict):
            redacted_dict, _ = self.redact_dict(data)
            return redacted_dict
        elif isinstance(data, list):
            return [self.redact_for_logging(item) for item in data]
        else:
            return data
