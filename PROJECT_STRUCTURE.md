# PsyAssist AI - Project Structure

## Overview
PsyAssist AI is a CrewAI-based multi-agent system for emergency emotional and psychotherapy support. This document outlines the complete project structure and architecture.

## 🏗️ Architecture

### Core Components
- **Multi-Agent System**: 6 specialized agents working together
- **State Machine**: Orchestrates session flow and agent transitions
- **Risk Assessment**: Continuous safety monitoring
- **Tool Adapters**: Pluggable external service integrations
- **Privacy Protection**: PII redaction and consent management
- **Observability**: Comprehensive event tracking and logging

### Session Flow
```
INIT → CONSENTED → TRIAGE → SUPPORT_LOOP ↔ RISK_CHECK → RESOURCES → CLOSE
                    ↓
                ESCALATE (if risk ≥ HIGH)
```

## 📁 Project Structure

```
psyassist/
├── __init__.py                 # Package initialization
├── agents/                     # CrewAI agent implementations
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── greeter.py             # Welcome and consent agent
│   ├── empathy.py             # Emotional support agent
│   ├── therapy_guide.py       # Coping techniques agent
│   ├── risk_assessment.py     # Safety monitoring agent
│   ├── resource.py            # Resource provider agent
│   └── escalation.py          # Human handoff agent
├── api/                       # FastAPI application
│   ├── __init__.py
│   └── main.py               # Main API endpoints
├── config/                    # Configuration management
│   ├── __init__.py
│   ├── settings.py           # Application settings
│   ├── prompts.py            # Agent prompt configurations
│   └── safety.py             # Safety rules and constraints
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── orchestrator.py       # Main system orchestrator
│   ├── session_manager.py    # Session management
│   └── state_machine.py      # State machine implementation
├── schemas/                   # Pydantic data models
│   ├── __init__.py
│   ├── session.py            # Session management schemas
│   ├── events.py             # Event tracking schemas
│   ├── risk.py               # Risk assessment schemas
│   └── resources.py          # Resource management schemas
├── tools/                     # Tool adapters
│   ├── __init__.py
│   ├── risk_classifier.py    # Risk assessment tool
│   ├── hotline_router.py     # Hotline routing tool
│   ├── warm_transfer.py      # Human handoff tool
│   ├── directory_lookup.py   # Resource directory tool
│   └── pii_redactor.py       # Privacy protection tool
└── workers/                   # Background task workers
    ├── __init__.py
    └── celery_app.py         # Celery task definitions

# Root level files
├── requirements.txt           # Python dependencies
├── README.md                 # Project documentation
├── env.example               # Environment configuration template
├── run.py                    # Server startup script
├── test_basic.py             # Basic system tests
└── PROJECT_STRUCTURE.md      # This file
```

## 🤖 Agents

### 1. Greeter Agent
- **Role**: Welcome users and obtain consent
- **Responsibilities**: 
  - Present service information
  - Collect explicit consent
  - Conduct initial triage
  - Handle emergency situations

### 2. Empathy Agent
- **Role**: Provide emotional support and active listening
- **Responsibilities**:
  - Reflective listening
  - Emotional validation
  - Grounding techniques
  - Risk monitoring

### 3. TherapyGuide Agent
- **Role**: Provide coping techniques and micro-interventions
- **Responsibilities**:
  - Evidence-based coping strategies
  - Step-by-step techniques
  - Crisis intervention
  - Safety monitoring

### 4. RiskAssessment Agent
- **Role**: Continuous safety monitoring
- **Responsibilities**:
  - Real-time risk assessment
  - Keyword pattern detection
  - Severity classification
  - Escalation triggers

### 5. Resource Agent
- **Role**: Provide support resources and information
- **Responsibilities**:
  - Resource directory lookup
  - Location-based recommendations
  - Crisis resource prioritization
  - Contact information

### 6. Escalation Agent
- **Role**: Handle transitions to human support
- **Responsibilities**:
  - Warm transfer coordination
  - Emergency response
  - Human counselor connection
  - Transfer status monitoring

## 🛠️ Tools

### Risk Classifier
- Keyword-based pattern matching
- AI-powered assessment (optional)
- Severity classification (NONE, LOW, MEDIUM, HIGH, CRITICAL)
- Confidence scoring

### PII Redactor
- Personal information detection
- Automatic redaction
- Mental health context awareness
- Hash-based recovery (optional)

### Hotline Router
- Geographic resource lookup
- Availability checking
- Emergency number routing
- Multi-language support

### Directory Lookup
- Resource categorization
- Location-based filtering
- Bundle recommendations
- Verification status

### Warm Transfer API
- Human counselor connection
- Transfer status tracking
- Context sharing
- Fallback handling

## 📊 Data Models

### Session Management
- Session lifecycle tracking
- State transitions
- Consent management
- Risk flag history

### Event Tracking
- System observability
- Risk assessment events
- Escalation tracking
- Performance metrics

### Risk Assessment
- Multi-factor analysis
- Confidence scoring
- Historical context
- Escalation triggers

### Resources
- Support service directory
- Geographic coverage
- Availability status
- Contact methods

## 🔒 Safety Features

### Risk Detection
- Real-time keyword monitoring
- Pattern recognition
- Contextual analysis
- Confidence thresholds

### Privacy Protection
- PII automatic redaction
- Consent-based data handling
- Data retention policies
- Secure transmission

### Escalation Protocols
- Immediate emergency response
- Human counselor connection
- Crisis resource prioritization
- Transfer status monitoring

## 🚀 Getting Started

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp env.example .env
# Edit .env with your settings
```

### 3. Run Tests
```bash
python test_basic.py
```

### 4. Start Server
```bash
python run.py
```

### 5. API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Application secret key
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `SESSION_TIMEOUT_MINUTES`: Session timeout
- `ESCALATION_THRESHOLD`: Risk escalation threshold
- `PII_REDACTION_ENABLED`: Privacy protection toggle

### Agent Configuration
- Prompt templates in `config/prompts.py`
- Safety rules and constraints
- Response style guidelines
- Tool integrations

## 📈 Monitoring

### Health Checks
- `/health`: Basic health status
- `/status`: System metrics
- Session cleanup monitoring
- Error tracking

### Event Tracking
- Session lifecycle events
- Risk assessment events
- Escalation events
- Performance metrics

## 🔄 State Machine

### Valid Transitions
- `INIT → CONSENTED`: User grants consent
- `CONSENTED → TRIAGE`: Initial assessment
- `TRIAGE → SUPPORT_LOOP`: Begin support
- `SUPPORT_LOOP ↔ RISK_CHECK`: Periodic safety checks
- `SUPPORT_LOOP → RESOURCES`: Resource requests
- `ANY → ESCALATE`: Risk-based escalation
- `ANY → CLOSE`: Session termination

### State Guards
- Consent validation
- Risk threshold checks
- Message count limits
- Timeout enforcement

## 🧪 Testing

### Test Coverage
- Basic session flow
- Risk assessment accuracy
- PII redaction effectiveness
- Agent interactions
- State transitions
- Error handling

### Test Types
- Unit tests for individual components
- Integration tests for agent interactions
- End-to-end session flow tests
- Safety and privacy tests

## 🚨 Safety Considerations

### Medical Disclaimer
⚠️ **This is not a medical device and cannot provide medical treatment.**

### Emergency Response
- Immediate escalation for high-risk situations
- Emergency number prioritization
- Human counselor connection
- Crisis resource provision

### Privacy Protection
- PII automatic redaction
- Consent-based data handling
- Secure data transmission
- Data retention policies

## 🔮 Future Enhancements

### Planned Features
- Multi-language support
- Advanced AI risk assessment
- Integration with EHR systems
- Mobile application
- Analytics dashboard
- Advanced reporting

### Scalability
- Database integration
- Message queue systems
- Load balancing
- Microservice architecture
- Cloud deployment

---

**Note**: This system is designed for emergency emotional support and should always be used in conjunction with professional mental health services. It is not a replacement for medical treatment or therapy.
