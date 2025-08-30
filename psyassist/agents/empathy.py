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
        
        # Check for aggressive language that might need escalation
        emotional_analysis = self._analyze_emotions(message)
        if emotional_analysis['is_aggressive']:
            # Trigger risk assessment for aggressive messages
            risk_assessment['should_escalate'] = True
            # Note: We can't modify enum values directly, but the risk assessment should handle this
        
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
        print(f"🔍 DEBUG: Analyzing emotions for: '{message_lower}'")
        
        emotions = {
            'sadness': ['sad', 'depressed', 'hopeless', 'worthless', 'empty', 'lonely', 'grief', 'сумно', 'сумний', 'депресія'],
            'anger': ['angry', 'furious', 'rage', 'hate', 'frustrated', 'irritated', 'mad', 'fuck', 'shit', 'damn', 'злий', 'зла', 'гнів'],
            'fear': ['afraid', 'scared', 'terrified', 'anxious', 'worried', 'panic', 'fear', 'страх', 'страшно', 'тривога'],
            'shame': ['ashamed', 'embarrassed', 'guilty', 'humiliated', 'worthless', 'сором', 'винний'],
            'confusion': ['confused', 'lost', 'unsure', 'uncertain', 'don\'t know', 'плутаюся', 'не знаю'],
            'overwhelm': ['overwhelmed', 'stressed', 'exhausted', 'tired', 'burned out', 'втомлений', 'стрес'],
            'isolation': ['alone', 'lonely', 'isolated', 'no one', 'nobody cares', 'самотній', 'самотно'],
            'hopelessness': ['hopeless', 'no point', 'nothing matters', 'give up', 'безнадійно', 'марно'],
            'happiness': ['happy', 'good', 'great', 'wonderful', 'amazing', 'excellent', 'радий', 'рада', 'добре', 'чудово', 'feel good', 'feeling good'],
            'calm': ['calm', 'peaceful', 'relaxed', 'tranquil', 'спокійний', 'спокійно', 'мирно'],
            'gratitude': ['thankful', 'grateful', 'appreciate', 'дякую', 'вдячний', 'thank you', 'thanks']
        }
        
        detected_emotions = {}
        for emotion, keywords in emotions.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_emotions[emotion] = True
                    print(f"✅ DEBUG: Found emotion '{emotion}' with keyword '{keyword}'")
                    break
        
        # Check for aggressive language
        aggressive_indicators = ['fuck', 'shit', 'damn', 'hate', 'kill', 'die', 'death', 'suicide', 'end it all', 'fuck you']
        is_aggressive = any(indicator in message_lower for indicator in aggressive_indicators)
        
        # Assess intensity
        intensity_indicators = {
            'high': ['very', 'extremely', 'completely', 'totally', 'absolutely', 'fuck', 'shit', 'damn'],
            'medium': ['really', 'quite', 'pretty', 'rather'],
            'low': ['a little', 'slightly', 'somewhat', 'kind of']
        }
        
        intensity = 'medium'  # default
        for level, indicators in intensity_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                intensity = level
                break
        
        # Determine primary emotion
        if is_aggressive:
            primary_emotion = 'anger'
        elif detected_emotions:
            primary_emotion = list(detected_emotions.keys())[0]
        else:
            primary_emotion = 'neutral'
        
        result = {
            'detected_emotions': detected_emotions,
            'intensity': intensity,
            'primary_emotion': primary_emotion,
            'is_aggressive': is_aggressive
        }
        print(f"🔍 DEBUG: Analysis result: {result}")
        return result
    
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
            'anger': "It's natural to feel angry when things aren't going the way you hoped. I can hear the intensity in your words.",
            'fear': "Fear is a very real and valid emotion, especially when facing uncertainty.",
            'shame': "Shame can be incredibly painful, and it's okay to feel this way.",
            'confusion': "It's normal to feel confused when things are unclear or uncertain.",
            'overwhelm': "Feeling overwhelmed is a natural response when there's too much to handle.",
            'isolation': "Feeling alone can be one of the most painful experiences.",
            'hopelessness': "When things feel hopeless, it can be incredibly difficult to see a way forward.",
            'happiness': "It's wonderful that you're feeling good! Positive emotions are just as important to acknowledge.",
            'calm': "It's great that you're feeling calm and peaceful. That's a healthy emotional state.",
            'gratitude': "Gratitude is such a beautiful emotion. It's wonderful that you're able to feel thankful."
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
