# PsyAssist AI

A CrewAI-based multi-agent system for emergency emotional and psychotherapy support.

⚠️ **Important**: This is **not a medical device**. The system must **never diagnose** or provide medical treatment. It offers empathetic listening, micro-coping techniques, and safe escalation to human professionals or hotlines.

## Features

- **Multi-Agent Support**: Greeter, Empathy, TherapyGuide, RiskAssessment, Resource, and Escalation agents
- **State Machine Orchestration**: Session flow with risk-based fast-pathing
- **Safety & Risk Handling**: Continuous risk assessment with automatic escalation
- **Privacy-First**: PII redaction and consent-based data handling
- **Observability**: Comprehensive logging and event tracking
- **Tool Adapters**: Pluggable components for risk classification, hotline routing, and more

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run the system**:
   ```bash
   # Start the API server
   uvicorn psyassist.api.main:app --reload
   
   # Start the Celery worker
   celery -A psyassist.workers.celery_app worker --loglevel=info
   ```

## Architecture

### Agents
- **Greeter**: Welcome, triage, and consent collection
- **Empathy**: Active listening and emotional grounding
- **TherapyGuide**: Micro-interventions and coping techniques
- **RiskAssessment**: Continuous risk monitoring
- **Resource**: Local hotlines and information
- **Escalation**: Hotline/human handoff

### Session Flow
```
INIT → CONSENTED → TRIAGE → SUPPORT_LOOP ↔ RISK_CHECK → RESOURCES → CLOSE
                    ↓
                ESCALATE (if risk ≥ HIGH)
```

### Safety Features
- Real-time risk assessment
- Automatic escalation for high-risk situations
- PII redaction before storage
- Consent-based data handling
- Emergency number prioritization for critical cases

## Development

### Project Structure
```
psyassist/
├── agents/           # CrewAI agent implementations
├── api/             # FastAPI application
├── core/            # Core business logic
├── schemas/         # Pydantic models and JSON schemas
├── tools/           # Tool adapters
├── workers/         # Celery tasks
└── config/          # Configuration and prompts
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/scenarios/
```

## Contributing

1. Follow the coding style guidelines
2. Write unit tests for new features
3. Ensure all safety guardrails are maintained
4. Update documentation as needed

## License

[Add your license here]

## Support

For technical support or questions about the system architecture, please open an issue in this repository.

**For mental health support**: Please contact your local mental health professionals or emergency services.
