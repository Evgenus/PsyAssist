"""
TherapyGuide agent for PsyAssist AI.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base_agent import BasePsyAssistAgent
from ..schemas.session import Session, SessionState
from ..schemas.events import EventType, EventPriority
from ..config.prompts import TherapyGuidePrompt


class TherapyGuideAgent(BasePsyAssistAgent):
    """TherapyGuide agent for providing coping techniques and micro-interventions."""
    
    def __init__(self, **kwargs):
        prompt_config = TherapyGuidePrompt()
        super().__init__(
            name="TherapyGuide",
            prompt_config=prompt_config,
            **kwargs
        )
    
    async def process_message(self, session: Session, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and provide coping techniques."""
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
        
        # Provide coping techniques
        coping_response = await self._provide_coping_techniques(session, message, context)
        
        # Update session
        session = self.update_session(session)
        
        return self.format_response(
            coping_response,
            {
                'coping_techniques_provided': True,
                'risk_assessed': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value
            }
        )
    
    async def _provide_coping_techniques(self, session: Session, message: str, context: Dict[str, Any]) -> str:
        """Provide appropriate coping techniques based on the user's situation."""
        # Analyze the situation
        situation_analysis = self._analyze_situation(message)
        
        # Select appropriate techniques
        techniques = self._select_techniques(situation_analysis)
        
        # Create response
        response = self._create_technique_response(techniques, situation_analysis)
        
        return response
    
    def _analyze_situation(self, message: str) -> Dict[str, Any]:
        """Analyze the user's situation to determine appropriate techniques."""
        message_lower = message.lower()
        
        # Identify triggers and stressors
        triggers = {
            'anxiety': ['anxious', 'worried', 'nervous', 'panic', 'stress'],
            'depression': ['sad', 'depressed', 'hopeless', 'worthless', 'empty'],
            'anger': ['angry', 'furious', 'rage', 'frustrated', 'irritated'],
            'overwhelm': ['overwhelmed', 'stressed', 'exhausted', 'too much'],
            'grief': ['loss', 'grief', 'death', 'missing', 'gone'],
            'trauma': ['trauma', 'abuse', 'assault', 'accident', 'ptsd']
        }
        
        detected_triggers = {}
        for trigger, keywords in triggers.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_triggers[trigger] = True
        
        # Assess urgency
        urgency_indicators = ['right now', 'immediately', 'urgent', 'can\'t take it']
        is_urgent = any(indicator in message_lower for indicator in urgency_indicators)
        
        return {
            'detected_triggers': detected_triggers,
            'primary_trigger': list(detected_triggers.keys())[0] if detected_triggers else 'general',
            'is_urgent': is_urgent,
            'message_length': len(message)
        }
    
    def _select_techniques(self, situation_analysis: Dict[str, Any]) -> list:
        """Select appropriate coping techniques based on the situation."""
        primary_trigger = situation_analysis['primary_trigger']
        is_urgent = situation_analysis['is_urgent']
        
        # Technique database
        techniques = {
            'anxiety': [
                {
                    'name': 'Deep Breathing',
                    'description': 'Take slow, deep breaths. Inhale for 4 counts, hold for 4, exhale for 4.',
                    'steps': ['Find a comfortable position', 'Place one hand on your chest, one on your belly', 'Breathe in slowly through your nose for 4 counts', 'Hold for 4 counts', 'Exhale slowly through your mouth for 4 counts', 'Repeat 5-10 times']
                },
                {
                    'name': '5-4-3-2-1 Grounding',
                    'description': 'Use your senses to ground yourself in the present moment.',
                    'steps': ['Name 5 things you can see', 'Name 4 things you can touch', 'Name 3 things you can hear', 'Name 2 things you can smell', 'Name 1 thing you can taste']
                }
            ],
            'depression': [
                {
                    'name': 'Small Steps',
                    'description': 'Break down overwhelming tasks into tiny, manageable steps.',
                    'steps': ['Identify one small thing you can do right now', 'Make it as small as possible (even just getting out of bed)', 'Celebrate completing that small step', 'Build from there']
                },
                {
                    'name': 'Self-Compassion',
                    'description': 'Treat yourself with the same kindness you would offer a friend.',
                    'steps': ['Acknowledge your pain without judgment', 'Remember that suffering is part of being human', 'Offer yourself kind words', 'Take a gentle action toward self-care']
                }
            ],
            'anger': [
                {
                    'name': 'Time Out',
                    'description': 'Take a brief pause before responding to intense emotions.',
                    'steps': ['Recognize the anger building', 'Take a step back physically if possible', 'Count to 10 slowly', 'Take deep breaths', 'Consider your response before acting']
                },
                {
                    'name': 'Physical Release',
                    'description': 'Release tension through safe physical activity.',
                    'steps': ['Go for a walk', 'Do some jumping jacks', 'Squeeze a stress ball', 'Write down your feelings', 'Talk to someone you trust']
                }
            ],
            'overwhelm': [
                {
                    'name': 'Priority Sorting',
                    'description': 'Organize tasks by importance and urgency.',
                    'steps': ['List everything you need to do', 'Mark each as urgent/not urgent and important/not important', 'Focus on urgent and important tasks first', 'Delegate or postpone less critical items']
                },
                {
                    'name': 'Mindful Pause',
                    'description': 'Take a moment to center yourself before continuing.',
                    'steps': ['Stop what you\'re doing', 'Take 3 deep breaths', 'Notice how you\'re feeling', 'Ask yourself what you need right now', 'Choose one small action']
                }
            ],
            'general': [
                {
                    'name': 'Progressive Muscle Relaxation',
                    'description': 'Systematically tense and relax muscle groups to reduce tension.',
                    'steps': ['Start with your toes', 'Tense the muscles for 5 seconds', 'Release and feel the relaxation', 'Move up to your calves, thighs, stomach, chest, arms, and face']
                },
                {
                    'name': 'Gratitude Practice',
                    'description': 'Focus on things you appreciate, no matter how small.',
                    'steps': ['Think of 3 things you\'re grateful for today', 'They can be as simple as a warm cup of coffee', 'Really feel the appreciation', 'Write them down if helpful']
                }
            ]
        }
        
        # Select techniques based on trigger
        selected_techniques = techniques.get(primary_trigger, techniques['general'])
        
        # If urgent, prioritize quick techniques
        if is_urgent:
            quick_techniques = [t for t in selected_techniques if 'breathing' in t['name'].lower() or 'grounding' in t['name'].lower()]
            if quick_techniques:
                selected_techniques = quick_techniques[:1]  # Just one quick technique
        
        return selected_techniques[:2]  # Limit to 2 techniques
    
    def _create_technique_response(self, techniques: list, situation_analysis: Dict[str, Any]) -> str:
        """Create a response that presents the coping techniques."""
        if not techniques:
            return "I'm here to support you. Sometimes just talking about what's going on can help. What would be most helpful for you right now?"
        
        response = "I'd like to share some coping techniques that might help you right now. "
        
        for i, technique in enumerate(techniques):
            response += f"\n\n{technique['name']}: {technique['description']}"
            
            if situation_analysis['is_urgent']:
                response += f"\nHere's how to do it: {technique['steps'][0]}"
            else:
                response += "\nHere's how to do it:"
                for step in technique['steps']:
                    response += f"\n• {step}"
        
        response += "\n\nRemember, these are suggestions - use what feels helpful to you. Would you like to try one of these, or would you prefer to talk more about what's going on?"
        
        return response
    
    async def _handle_escalation(self, session: Session, message: str, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Handle situations that require escalation."""
        # Update session state
        session.state = SessionState.ESCALATE
        session.metadata['escalation_triggered'] = True
        session = self.update_session(session)
        
        # Create escalation response
        escalation_response = (
            "I'm concerned about what you're sharing, and I want to make sure you get the support you need. "
            "While coping techniques can be helpful, I think you would benefit from talking with a trained counselor "
            "who can provide more specialized support. Would you be open to that?"
        )
        
        return self.format_response(
            escalation_response,
            {
                'escalation_triggered': True,
                'risk_level': risk_assessment['assessment'].overall_severity.value,
                'next_state': SessionState.ESCALATE.value
            }
        )
