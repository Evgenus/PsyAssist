"""
Empathy agent for PsyAssist AI.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base_agent import BasePsyAssistAgent
from ..schemas.session import Session, SessionState
from ..schemas.events import EventType, EventPriority
from ..config.prompts import EmpathyPrompt


class EmpathyAgent(BasePsyAssistAgent):
    """Empathy agent for active listening and emotional support."""
    
    def __init__(self, **kwargs):
        prompt_config = EmpathyPrompt()
        super().__init__(
            name="Empathy",
            prompt_config=prompt_config,
            **kwargs
        )
    
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and return an empathetic response."""
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
        
        # Process with empathy
        empathetic_response = await self._create_empathetic_response(session, message, context)
        
        # Update session
        session = self.update_session(session)
        
        return self.format_response(
            empathetic_response,
            {
                'empathy_provided': True,
                'risk_assessed': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value
            }
        )
    
    async def _create_empathetic_response(self, session: Session, message: str, context: Dict[str, Any]) -> str:
        """Create an empathetic response to the user's message."""
        # Analyze emotional content
        emotional_analysis = self._analyze_emotions(message)
        
        # Create reflective response
        reflective_response = self._create_reflective_response(message, emotional_analysis)
        
        # Add validation
        validation_response = self._add_emotional_validation(emotional_analysis)
        
        # Add grounding if needed
        grounding_response = self._add_grounding_if_needed(emotional_analysis)
        
        # Combine responses
        full_response = f"{reflective_response} {validation_response}"
        if grounding_response:
            full_response += f" {grounding_response}"
        
        return full_response
    
    def _analyze_emotions(self, message: str) -> Dict[str, Any]:
        """Analyze the emotional content of the message."""
        message_lower = message.lower()
        
        emotions = {
            'sadness': ['sad', 'depressed', 'hopeless', 'worthless', 'empty', 'lonely', 'grief'],
            'anger': ['angry', 'furious', 'rage', 'hate', 'frustrated', 'irritated', 'mad'],
            'fear': ['afraid', 'scared', 'terrified', 'anxious', 'worried', 'panic', 'fear'],
            'shame': ['ashamed', 'embarrassed', 'guilty', 'humiliated', 'worthless'],
            'confusion': ['confused', 'lost', 'unsure', 'uncertain', 'don\'t know'],
            'overwhelm': ['overwhelmed', 'stressed', 'exhausted', 'tired', 'burned out'],
            'isolation': ['alone', 'lonely', 'isolated', 'no one', 'nobody cares'],
            'hopelessness': ['hopeless', 'no point', 'nothing matters', 'give up']
        }
        
        detected_emotions = {}
        for emotion, keywords in emotions.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_emotions[emotion] = True
        
        # Assess intensity
        intensity_indicators = {
            'high': ['very', 'extremely', 'completely', 'totally', 'absolutely'],
            'medium': ['really', 'quite', 'pretty', 'rather'],
            'low': ['a little', 'slightly', 'somewhat', 'kind of']
        }
        
        intensity = 'medium'  # default
        for level, indicators in intensity_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                intensity = level
                break
        
        return {
            'detected_emotions': detected_emotions,
            'intensity': intensity,
            'primary_emotion': list(detected_emotions.keys())[0] if detected_emotions else 'neutral'
        }
    
    def _create_reflective_response(self, message: str, emotional_analysis: Dict[str, Any]) -> str:
        """Create a reflective response that mirrors the user's emotions."""
        primary_emotion = emotional_analysis['primary_emotion']
        intensity = emotional_analysis['intensity']
        
        # Extract key phrases for reflection
        key_phrases = self._extract_key_phrases(message)
        
        # Create reflection
        if key_phrases:
            reflection = f"It sounds like you're feeling {primary_emotion}, and you're saying that {key_phrases[0]}"
        else:
            reflection = f"It sounds like you're feeling {primary_emotion}"
        
        # Adjust intensity
        if intensity == 'high':
            reflection += " very deeply"
        elif intensity == 'low':
            reflection += " a little"
        
        reflection += "."
        
        return reflection
    
    def _extract_key_phrases(self, message: str) -> list:
        """Extract key phrases from the message for reflection."""
        # Simple phrase extraction - in a real implementation, this would be more sophisticated
        phrases = []
        
        # Look for "I feel" statements
        if "i feel" in message.lower():
            start = message.lower().find("i feel")
            end = message.find(".", start)
            if end == -1:
                end = len(message)
            phrase = message[start:end].strip()
            phrases.append(phrase)
        
        # Look for "I am" statements
        if "i am" in message.lower():
            start = message.lower().find("i am")
            end = message.find(".", start)
            if end == -1:
                end = len(message)
            phrase = message[start:end].strip()
            phrases.append(phrase)
        
        return phrases
    
    def _add_emotional_validation(self, emotional_analysis: Dict[str, Any]) -> str:
        """Add emotional validation to the response."""
        primary_emotion = emotional_analysis['primary_emotion']
        
        validation_statements = {
            'sadness': "It's completely understandable to feel sad when going through difficult times.",
            'anger': "It's natural to feel angry when things aren't going the way you hoped.",
            'fear': "Fear is a very real and valid emotion, especially when facing uncertainty.",
            'shame': "Shame can be incredibly painful, and it's okay to feel this way.",
            'confusion': "It's normal to feel confused when things are unclear or uncertain.",
            'overwhelm': "Feeling overwhelmed is a natural response when there's too much to handle.",
            'isolation': "Feeling alone can be one of the most painful experiences.",
            'hopelessness': "When things feel hopeless, it can be incredibly difficult to see a way forward."
        }
        
        return validation_statements.get(primary_emotion, "Your feelings are valid and important.")
    
    def _add_grounding_if_needed(self, emotional_analysis: Dict[str, Any]) -> str:
        """Add grounding techniques if the user seems overwhelmed."""
        if emotional_analysis['intensity'] == 'high' or 'overwhelm' in emotional_analysis['detected_emotions']:
            return "Would it help to take a moment to breathe? You can try taking a slow, deep breath in through your nose and out through your mouth."
        
        return ""
    
    async def _handle_escalation(self, session: Session, message: str, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Handle situations that require escalation."""
        # Update session state
        session.state = SessionState.ESCALATE
        session.metadata['escalation_triggered'] = True
        session = self.update_session(session)
        
        # Create escalation response
        escalation_response = (
            "I'm concerned about what you're sharing, and I want to make sure you get the support you need. "
            "I think it would be helpful to connect you with a trained counselor who can provide more specialized support. "
            "Would you be open to that?"
        )
        
        return self.format_response(
            escalation_response,
            {
                'escalation_triggered': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value,
                'next_state': SessionState.ESCALATE.value
            }
        )
