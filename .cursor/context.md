# PsyAssist AI — Project Context for Cursor

## Overview
We are building **PsyAssist AI**, a CrewAI-based multi-agent system that provides **emergency emotional and psychotherapy support**.  
⚠️ This is **not a medical device**. The system must **never diagnose** or provide medical treatment.  
It offers **empathetic listening, micro-coping techniques, and safe escalation** to human professionals or hotlines.  

---

## Tasks

### 1. Agent Implementation
- Implement CrewAI agents:  
  - **Greeter** (welcome, triage, consent)  
  - **Empathy** (active listening, grounding)  
  - **TherapyGuide** (micro-interventions)  
  - **RiskAssessment** (continuous sentinel)  
  - **Resource** (local hotlines, info)  
  - **Escalation** (hotline/human handoff)  
- Each agent must follow **goals, constraints, and safety guardrails** from PRD.  
- Use tool adapters instead of hardcoding (see below).  

### 2. Orchestration / State Machine
- Session flow:  
  `INIT → CONSENTED → TRIAGE → SUPPORT_LOOP ↔ RISK_CHECK → RESOURCES → CLOSE`  
- **Fast-path:** Any state → ESCALATE if risk severity ≥ HIGH or user explicitly requests help.  
- Include timeouts, opt-outs, and message caps.  

### 3. Schemas & Contracts
- Implement JSON schemas for messages/events:  
  - `triage_summary`  
  - `support_turn`  
  - `technique_step`  
  - `risk_assessment`  
  - `resource_bundle`  
  - `escalation_plan`  
- Validate all outputs against schemas.  

### 4. Safety & Risk Handling
- Integrate **risk classifier** + keyword/pattern rules.  
- If severity ≥ HIGH → route to Escalation Agent immediately.  
- For CRITICAL → instruct user to call local emergency number first.  

### 5. Tool Adapters
Create pluggable adapters with clear interfaces + unit tests:  
- `RiskClassifier`  
- `HotlineRouter`  
- `WarmTransferAPI`  
- `DirectoryLookup` (per locale)  
- `PIIRedactor`  

### 6. Observability & Logging
- Emit events to event bus (NATS/Kafka):  
  - `session.created`, `session.updated`, `risk.assessed`, `escalation.triggered`  
- Redact PII before persistence.  
- Track metrics: risk flags, escalations, transfer success, opt-outs.  

### 7. Compliance & Privacy
- Session start must include **consent flow**.  
- Default: **no storage** unless user opts in.  
- Run `PIIRedactor` before storing or logging data.  

---

## Coding Style
- Use **dependency injection** for services/tools.  
- Keep prompts & safety rules in **external config files**.  
- Prefer **short, trauma-informed** responses.  
- Write **unit + scenario tests** (esp. risk decision logic).  

---

## Deliverables Checklist
- [ ] CrewAI agents & tasks implemented  
- [ ] State machine orchestration service  
- [ ] Tool adapters + tests  
- [ ] JSON schemas for events  
- [ ] Prompts & safety configs externalized  
- [ ] Observability dashboards + alerts  
- [ ] Test suite: unit, scenario, adversarial  

---

## Cursor Instructions
- Always follow this context when generating code.  
- Default framework: **Python + CrewAI**.  
- API layer: **FastAPI** (for gateway).  
- Event system: **Celery**.  
- Database: simple **KVS (Redis/SQLite)** for MVP.
- User **Mem0** for storing history of communication
