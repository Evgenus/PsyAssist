"""
Risk classifier tool for PsyAssist AI safety system.
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from ..schemas.risk import RiskAssessment, RiskFactor, RiskCategory, RiskSeverity, RiskKeywords
from ..config.settings import settings


class BaseRiskClassifier(ABC):
    """Abstract base class for risk classifiers."""
    
    @abstractmethod
    async def assess_risk(self, text: str, context: Dict[str, Any] = None) -> RiskAssessment:
        """Assess risk level in given text."""
        pass
    
    @abstractmethod
    async def classify_keywords(self, text: str) -> List[RiskFactor]:
        """Classify risk keywords in text."""
        pass


class KeywordBasedRiskClassifier(BaseRiskClassifier):
    """Keyword-based risk classifier implementation."""
    
    def __init__(self, keywords: RiskKeywords = None):
        self.keywords = keywords or RiskKeywords()
        self._build_patterns()
    
    def _build_patterns(self):
        """Build regex patterns for keyword detection."""
        self.patterns = {}
        
        # Build patterns for each category
        category_keywords = {
            RiskCategory.SUICIDE: self.keywords.suicide_keywords,
            RiskCategory.SELF_HARM: self.keywords.self_harm_keywords,
            RiskCategory.HARM_TO_OTHERS: self.keywords.harm_to_others_keywords,
            RiskCategory.CRISIS: self.keywords.crisis_keywords,
        }
        
        for category, keywords in category_keywords.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.patterns[category] = re.compile(pattern, re.IGNORECASE)
        
        # Build complex patterns
        for pattern_name, pattern_str in self.keywords.patterns.items():
            self.patterns[pattern_name] = re.compile(pattern_str, re.IGNORECASE)
    
    async def assess_risk(self, text: str, context: Dict[str, Any] = None) -> RiskAssessment:
        """Assess overall risk level in text."""
        context = context or {}
        
        # Classify individual risk factors
        risk_factors = await self.classify_keywords(text)
        
        # Determine overall severity
        overall_severity = self._determine_overall_severity(risk_factors, context)
        overall_confidence = self._calculate_confidence(risk_factors, context)
        
        # Create assessment
        assessment = RiskAssessment(
            assessment_id=f"risk_{datetime.utcnow().isoformat()}",
            session_id=context.get('session_id', 'unknown'),
            overall_severity=overall_severity,
            overall_confidence=overall_confidence,
            risk_factors=risk_factors,
            assessor="KeywordBasedRiskClassifier",
            model_used="keyword_pattern_matching"
        )
        
        return assessment
    
    async def classify_keywords(self, text: str) -> List[RiskFactor]:
        """Classify risk keywords in text."""
        risk_factors = []
        text_lower = text.lower()
        
        # Check each category
        category_keywords = {
            RiskCategory.SUICIDE: self.keywords.suicide_keywords,
            RiskCategory.SELF_HARM: self.keywords.self_harm_keywords,
            RiskCategory.HARM_TO_OTHERS: self.keywords.harm_to_others_keywords,
            RiskCategory.CRISIS: self.keywords.crisis_keywords,
        }
        
        for category, keywords in category_keywords.items():
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
            
            if found_keywords:
                severity = self._determine_severity_for_category(category, found_keywords, text)
                confidence = self._calculate_category_confidence(category, found_keywords, text)
                
                risk_factor = RiskFactor(
                    category=category,
                    severity=severity,
                    confidence=confidence,
                    keywords=found_keywords,
                    context=self._extract_context(text, found_keywords)
                )
                risk_factors.append(risk_factor)
        
        # Check complex patterns
        for pattern_name, pattern in self.keywords.patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                # Map pattern to category
                category = self._map_pattern_to_category(pattern_name)
                severity = RiskSeverity.HIGH if 'immediate' in pattern_name else RiskSeverity.MEDIUM
                
                risk_factor = RiskFactor(
                    category=category,
                    severity=severity,
                    confidence=0.8,
                    keywords=[pattern_name],
                    context=f"Pattern match: {pattern_name}"
                )
                risk_factors.append(risk_factor)
        
        return risk_factors
    
    def _determine_severity_for_category(self, category: RiskCategory, keywords: List[str], text: str) -> RiskSeverity:
        """Determine severity level for a specific category."""
        # Base severity mapping
        base_severity = {
            RiskCategory.SUICIDE: RiskSeverity.HIGH,
            RiskCategory.SELF_HARM: RiskSeverity.MEDIUM,
            RiskCategory.HARM_TO_OTHERS: RiskSeverity.HIGH,
            RiskCategory.CRISIS: RiskSeverity.MEDIUM,
        }
        
        severity = base_severity.get(category, RiskSeverity.LOW)
        
        # Adjust based on context
        text_lower = text.lower()
        
        # Immediate/urgent indicators
        immediate_indicators = ['now', 'tonight', 'today', 'immediately', 'right now']
        if any(indicator in text_lower for indicator in immediate_indicators):
            if severity == RiskSeverity.MEDIUM:
                severity = RiskSeverity.HIGH
            elif severity == RiskSeverity.HIGH:
                severity = RiskSeverity.CRITICAL
        
        # Plan indicators
        plan_indicators = ['plan', 'going to', 'will', 'intend', 'decided']
        if any(indicator in text_lower for indicator in plan_indicators):
            if severity == RiskSeverity.LOW:
                severity = RiskSeverity.MEDIUM
            elif severity == RiskSeverity.MEDIUM:
                severity = RiskSeverity.HIGH
        
        # Means indicators
        means_indicators = ['gun', 'pills', 'rope', 'knife', 'weapon']
        if any(indicator in text_lower for indicator in means_indicators):
            if severity == RiskSeverity.MEDIUM:
                severity = RiskSeverity.HIGH
            elif severity == RiskSeverity.HIGH:
                severity = RiskSeverity.CRITICAL
        
        return severity
    
    def _calculate_category_confidence(self, category: RiskCategory, keywords: List[str], text: str) -> float:
        """Calculate confidence level for a category."""
        base_confidence = 0.6
        
        # Increase confidence with more keywords
        keyword_bonus = min(len(keywords) * 0.1, 0.3)
        
        # Increase confidence for specific, unambiguous keywords
        specific_keywords = ['suicide', 'kill myself', 'end my life']
        if any(kw in keywords for kw in specific_keywords):
            keyword_bonus += 0.2
        
        # Decrease confidence for ambiguous context
        ambiguous_indicators = ['joke', 'just kidding', 'not really', 'metaphor']
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in ambiguous_indicators):
            keyword_bonus -= 0.2
        
        return min(base_confidence + keyword_bonus, 1.0)
    
    def _determine_overall_severity(self, risk_factors: List[RiskFactor], context: Dict[str, Any]) -> RiskSeverity:
        """Determine overall severity from individual risk factors."""
        if not risk_factors:
            return RiskSeverity.NONE
        
        # Get the highest severity
        severities = [factor.severity for factor in risk_factors]
        severity_order = {
            RiskSeverity.NONE: 0,
            RiskSeverity.LOW: 1,
            RiskSeverity.MEDIUM: 2,
            RiskSeverity.HIGH: 3,
            RiskSeverity.CRITICAL: 4
        }
        
        max_severity = max(severities, key=lambda s: severity_order[s])
        
        # Consider context factors
        if context.get('previous_risk_level') == RiskSeverity.HIGH:
            # Escalate if there's a history of high risk
            if max_severity == RiskSeverity.MEDIUM:
                max_severity = RiskSeverity.HIGH
        
        return max_severity
    
    def _calculate_confidence(self, risk_factors: List[RiskFactor], context: Dict[str, Any]) -> float:
        """Calculate overall confidence level."""
        if not risk_factors:
            return 0.0
        
        # Weighted average of individual confidences
        total_weight = 0
        weighted_sum = 0
        
        for factor in risk_factors:
            # Weight by severity
            severity_weight = {
                RiskSeverity.NONE: 0,
                RiskSeverity.LOW: 1,
                RiskSeverity.MEDIUM: 2,
                RiskSeverity.HIGH: 3,
                RiskSeverity.CRITICAL: 4
            }[factor.severity]
            
            weighted_sum += factor.confidence * severity_weight
            total_weight += severity_weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _extract_context(self, text: str, keywords: List[str]) -> str:
        """Extract context around keywords."""
        if not keywords:
            return ""
        
        # Find the first keyword and extract surrounding context
        for keyword in keywords:
            if keyword.lower() in text.lower():
                start = max(0, text.lower().find(keyword.lower()) - 50)
                end = min(len(text), text.lower().find(keyword.lower()) + len(keyword) + 50)
                return text[start:end].strip()
        
        return ""
    
    def _map_pattern_to_category(self, pattern_name: str) -> RiskCategory:
        """Map pattern name to risk category."""
        pattern_mapping = {
            'suicide_plan': RiskCategory.SUICIDE,
            'immediate_risk': RiskCategory.CRISIS,
            'means_available': RiskCategory.SUICIDE,
        }
        return pattern_mapping.get(pattern_name, RiskCategory.OTHER)


class AIRiskClassifier(BaseRiskClassifier):
    """AI-powered risk classifier using LLM."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.keyword_classifier = KeywordBasedRiskClassifier()
    
    async def assess_risk(self, text: str, context: Dict[str, Any] = None) -> RiskAssessment:
        """Assess risk using AI model."""
        context = context or {}
        
        # First, use keyword classifier for immediate detection
        keyword_assessment = await self.keyword_classifier.assess_risk(text, context)
        
        # If high risk detected, return immediately
        if keyword_assessment.overall_severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]:
            return keyword_assessment
        
        # Otherwise, use AI for nuanced assessment
        if self.llm_client:
            return await self._ai_assessment(text, context, keyword_assessment)
        
        return keyword_assessment
    
    async def _ai_assessment(self, text: str, context: Dict[str, Any], keyword_assessment: RiskAssessment) -> RiskAssessment:
        """Perform AI-based risk assessment."""
        # This would integrate with an LLM for more nuanced assessment
        # For now, return the keyword assessment
        return keyword_assessment
    
    async def classify_keywords(self, text: str) -> List[RiskFactor]:
        """Classify keywords using keyword-based approach."""
        return await self.keyword_classifier.classify_keywords(text)


class RiskClassifier:
    """Main risk classifier interface."""
    
    def __init__(self, classifier_type: str = "keyword"):
        self.classifier_type = classifier_type
        
        if classifier_type == "keyword":
            self.classifier = KeywordBasedRiskClassifier()
        elif classifier_type == "ai":
            self.classifier = AIRiskClassifier()
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")
    
    async def assess_risk(self, text: str, context: Dict[str, Any] = None) -> RiskAssessment:
        """Assess risk in text."""
        return await self.classifier.assess_risk(text, context)
    
    async def classify_keywords(self, text: str) -> List[RiskFactor]:
        """Classify risk keywords in text."""
        return await self.classifier.classify_keywords(text)
    
    def should_escalate(self, assessment: RiskAssessment) -> bool:
        """Determine if escalation is needed based on assessment."""
        escalation_threshold = RiskSeverity(settings.escalation_threshold)
        return assessment.overall_severity >= escalation_threshold and assessment.overall_confidence >= 0.7
    
    def is_emergency(self, assessment: RiskAssessment) -> bool:
        """Determine if emergency response is needed."""
        emergency_threshold = RiskSeverity(settings.emergency_threshold)
        return assessment.overall_severity >= emergency_threshold and assessment.overall_confidence >= 0.8
