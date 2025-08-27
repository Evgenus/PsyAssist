# PsyAssist AI

A CrewAI-based multi-agent system for emergency emotional and psychotherapy support.

⚠️ **Important**: This is **not a medical device**. The system must **never diagnose** or provide medical treatment. It offers empathetic listening, micro-coping techniques, and safe escalation to human professionals or hotlines.

## Features

- **Multi-Agent Support**: Greeter, Empathy, TherapyGuide, RiskAssessment, Resource, and Escalation agents
- **State Machine Orchestration**: Session flow with risk-based fast-pathing
- **Safety & Risk Handling**: Continuous risk assessment with automatic escalation
- **Privacy-First**: PII redaction and consent-based data handling
- **Tool Adapters**: Pluggable components for risk classification, hotline routing, and more

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Python 3.12 or higher

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Evgenus/PsyAssist.git
   cd PsyAssist
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the system**:
   ```bash
   # Start the API server
   python run.py
   
   ```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Set your API keys
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f psyassist
```

### Using Docker directly

```bash
# Build the image
docker build -t psyassist .

# Run with Redis
docker run -p 8000:8000 --env-file .env psyassist
```

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Create a Session
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "metadata": {"location": "US"}}'
```

### Send a Message
```bash
curl -X POST http://localhost:8000/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "I need some help today"}'
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Required
SECRET_KEY=your-super-secret-key-here
OPENAI_API_KEY=your-openai-api-key

# Optional
ANTHROPIC_API_KEY=your-anthropic-api-key
DEBUG=false
SESSION_TIMEOUT_MINUTES=30
ESCALATION_THRESHOLD=HIGH
```

## Architecture

### Agents
- **Greeter**: Welcome, triage, and consent collection
- **Empathy**: Active listening and emotional grounding
- **TherapyGuide**: Coping techniques and micro-interventions
- **RiskAssessment**: Continuous safety monitoring
- **Resource**: Support resources and information
- **Escalation**: Human handoff and emergency response

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
└── config/          # Configuration and prompts
```

### Testing

```bash
# Run basic tests
python test_basic.py

# Run interactive demo
python -m psyassist.cli demo
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For technical support or questions about the system architecture, please open an issue in this repository.

**For mental health support**: Please contact your local mental health professionals or emergency services.
