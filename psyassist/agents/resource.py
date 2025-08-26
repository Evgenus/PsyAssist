"""
Resource agent for PsyAssist AI.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BasePsyAssistAgent
from ..schemas.session import Session, SessionState
from ..schemas.events import EventType, EventPriority
from ..schemas.resources import Resource, ResourceCategory
from ..config.prompts import ResourcePrompt
from ..tools import DirectoryLookup


class ResourceAgent(BasePsyAssistAgent):
    """Resource agent for providing support resources and information."""
    
    def __init__(self, directory_lookup: DirectoryLookup = None, **kwargs):
        prompt_config = ResourcePrompt()
        super().__init__(
            name="Resource",
            prompt_config=prompt_config,
            **kwargs
        )
        self.directory_lookup = directory_lookup or DirectoryLookup()
    
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and provide relevant resources."""
        context = context or {}
        
        # Validate session
        if not self.validate_session(session):
            return self.format_response(
                "I'm sorry, but this session has expired or reached its limit. Please start a new session.",
                {'error': 'session_invalid'}
            )
        
        # Assess risk first
        risk_assessment = await self.assess_risk(message, session)
        
        # Handle high-risk situations
        if risk_assessment['should_escalate']:
            return await self._handle_escalation(session, message, risk_assessment)
        
        # Provide resources
        resource_response = await self._provide_resources(session, message, context)
        
        # Update session
        session = self.update_session(session)
        
        return self.format_response(
            resource_response,
            {
                'resources_provided': True,
                'risk_assessed': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value
            }
        )
    
    async def _provide_resources(self, session: Session, message: str, context: Dict[str, Any]) -> str:
        """Provide relevant resources based on the user's needs."""
        # Analyze user needs
        needs_analysis = self._analyze_needs(message)
        
        # Get user location
        location = session.metadata.get('location', 'US')
        
        # Find appropriate resources
        resources = await self._find_resources(location, needs_analysis)
        
        # Create response
        response = self._create_resource_response(resources, needs_analysis)
        
        return response
    
    def _analyze_needs(self, message: str) -> Dict[str, Any]:
        """Analyze the user's needs to determine appropriate resources."""
        message_lower = message.lower()
        
        # Identify resource categories needed
        categories = {
            'crisis': ['crisis', 'emergency', 'urgent', 'immediate', 'right now'],
            'suicide_prevention': ['suicide', 'kill myself', 'end my life', 'want to die'],
            'mental_health': ['therapy', 'counseling', 'mental health', 'depression', 'anxiety'],
            'domestic_violence': ['abuse', 'domestic violence', 'partner', 'relationship violence'],
            'substance_abuse': ['alcohol', 'drugs', 'addiction', 'substance', 'recovery'],
            'general_support': ['help', 'support', 'talk', 'someone to talk to']
        }
        
        detected_needs = {}
        for need, keywords in categories.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_needs[need] = True
        
        # Determine urgency
        urgency_indicators = ['right now', 'immediately', 'urgent', 'emergency', 'crisis']
        is_urgent = any(indicator in message_lower for indicator in urgency_indicators)
        
        return {
            'detected_needs': detected_needs,
            'primary_need': list(detected_needs.keys())[0] if detected_needs else 'general_support',
            'is_urgent': is_urgent
        }
    
    async def _find_resources(self, location: str, needs_analysis: Dict[str, Any]) -> List[Resource]:
        """Find appropriate resources based on needs and location."""
        primary_need = needs_analysis['primary_need']
        is_urgent = needs_analysis['is_urgent']
        
        # Map needs to resource categories
        need_to_category = {
            'crisis': [ResourceCategory.CRISIS_INTERVENTION.value],
            'suicide_prevention': [ResourceCategory.SUICIDE_PREVENTION.value],
            'mental_health': [ResourceCategory.MENTAL_HEALTH.value],
            'domestic_violence': [ResourceCategory.DOMESTIC_VIOLENCE.value],
            'substance_abuse': [ResourceCategory.SUBSTANCE_ABUSE.value],
            'general_support': [ResourceCategory.GENERAL_SUPPORT.value]
        }
        
        categories = need_to_category.get(primary_need, [ResourceCategory.GENERAL_SUPPORT.value])
        
        # Get resources
        resources = await self.directory_lookup.get_resources(location, categories)
        
        # If urgent, prioritize crisis resources
        if is_urgent:
            crisis_resources = await self.directory_lookup.get_crisis_resources(location)
            if crisis_resources:
                resources = crisis_resources + resources
        
        # Limit to top 3 resources
        return resources[:3]
    
    def _create_resource_response(self, resources: List[Resource], needs_analysis: Dict[str, Any]) -> str:
        """Create a response that presents the resources."""
        if not resources:
            return "I'm here to support you. Sometimes just talking about what's going on can help. What would be most helpful for you right now?"
        
        response = "I'd like to share some resources that might be helpful for you. "
        
        if needs_analysis['is_urgent']:
            response += "Since this seems urgent, here are some immediate support options: "
        
        for i, resource in enumerate(resources, 1):
            response += f"\n\n{i}. {resource.name}"
            response += f"\n   {resource.description}"
            
            if resource.phone_number:
                response += f"\n   Phone: {resource.phone_number}"
            if resource.text_number:
                response += f"\n   Text: {resource.text_number}"
            if resource.website:
                response += f"\n   Website: {resource.website}"
            
            if resource.hours:
                response += f"\n   Hours: {resource.hours}"
            if resource.cost:
                response += f"\n   Cost: {resource.cost}"
        
        response += "\n\nThese resources are here to help. You can reach out to any of them when you're ready. "
        response += "Would you like me to help you find more specific resources, or would you prefer to talk more about what's going on?"
        
        return response
    
    async def _handle_escalation(self, session: Session, message: str, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Handle situations that require escalation."""
        # Update session state
        session.state = SessionState.ESCALATE
        session.metadata['escalation_triggered'] = True
        session = self.update_session(session)
        
        # Get emergency resources
        location = session.metadata.get('location', 'US')
        emergency_resources = await self.directory_lookup.get_crisis_resources(location)
        
        # Create escalation response
        escalation_response = (
            "I'm concerned about what you're sharing, and I want to make sure you get the support you need. "
            "Here are some immediate resources that can help: "
        )
        
        if emergency_resources:
            escalation_response += f"\n\n{emergency_resources[0].name}: {emergency_resources[0].description}"
            if emergency_resources[0].phone_number:
                escalation_response += f"\nPhone: {emergency_resources[0].phone_number}"
            if emergency_resources[0].text_number:
                escalation_response += f"\nText: {emergency_resources[0].text_number}"
        
        escalation_response += "\n\nI think it would be helpful to connect you with a trained counselor. Would you be open to that?"
        
        return self.format_response(
            escalation_response,
            {
                'escalation_triggered': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value,
                'next_state': SessionState.ESCALATE.value,
                'emergency_resources_provided': bool(emergency_resources)
            }
        )
