"""
Main FastAPI application for PsyAssist AI.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio

from ..core.orchestrator import PsyAssistOrchestrator
from ..schemas.session import Session, SessionUpdate
from ..schemas.risk import RiskAssessment
from ..config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="PsyAssist AI",
    description="A CrewAI-based multi-agent system for emergency emotional and psychotherapy support",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create orchestrator instance
orchestrator = PsyAssistOrchestrator()

# Request/Response models
class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class RiskAssessmentRequest(BaseModel):
    text: str

class EscalationRequest(BaseModel):
    resource_id: str

class ResourceRequest(BaseModel):
    categories: Optional[List[str]] = None

# Dependency to get orchestrator
def get_orchestrator() -> PsyAssistOrchestrator:
    return orchestrator

# Background task for cleanup
async def cleanup_expired_sessions():
    """Background task to clean up expired sessions."""
    while True:
        try:
            count = await orchestrator.cleanup_expired_sessions()
            if count > 0:
                print(f"Cleaned up {count} expired sessions")
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
        
        await asyncio.sleep(60)  # Run every minute

@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    # Start background cleanup task
    asyncio.create_task(cleanup_expired_sessions())

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PsyAssist AI",
        "version": "0.1.0"
    }

# System status endpoint
@app.get("/status")
async def system_status(orch: PsyAssistOrchestrator = Depends(get_orchestrator)):
    """Get system status."""
    return await orch.get_system_status()

# Session management endpoints
@app.post("/sessions", response_model=Dict[str, Any])
async def create_session(
    request: CreateSessionRequest,
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Create a new session."""
    try:
        session = await orch.create_session(
            user_id=request.user_id,
            metadata=request.metadata
        )
        return {
            "session_id": session.session_id,
            "status": "created",
            "expires_at": session.expires_at.isoformat() if session.expires_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Get session information."""
    session = await orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "state": session.state.value,
        "consent_status": session.consent_status.value,
        "message_count": session.message_count,
        "risk_flags": session.risk_flags,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "metadata": session.metadata
    }

@app.put("/sessions/{session_id}", response_model=Dict[str, Any])
async def update_session(
    session_id: str,
    updates: SessionUpdate,
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Update session information."""
    session = await orch.update_session(session_id, updates)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "status": "updated",
        "state": session.state.value
    }

@app.delete("/sessions/{session_id}")
async def close_session(
    session_id: str,
    reason: str = "user_requested",
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Close a session."""
    success = await orch.close_session(session_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "closed", "session_id": session_id}

# Message processing endpoint
@app.post("/sessions/{session_id}/messages", response_model=Dict[str, Any])
async def process_message(
    session_id: str,
    request: MessageRequest,
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Process a user message."""
    try:
        response = await orch.process_message(
            session_id=session_id,
            message=request.message,
            context=request.context
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Risk assessment endpoint
@app.post("/sessions/{session_id}/risk-assessment", response_model=Dict[str, Any])
async def assess_risk(
    session_id: str,
    request: RiskAssessmentRequest,
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Perform risk assessment on text."""
    try:
        assessment = await orch.assess_risk(session_id, request.text)
        return {
            "assessment_id": assessment.assessment_id,
            "overall_severity": assessment.overall_severity.value,
            "overall_confidence": assessment.overall_confidence,
            "risk_factors": [
                {
                    "category": factor.category.value,
                    "severity": factor.severity.value,
                    "confidence": factor.confidence,
                    "keywords": factor.keywords
                }
                for factor in assessment.risk_factors
            ],
            "assessed_at": assessment.assessed_at.isoformat(),
            "escalation_triggered": assessment.escalation_triggered,
            "emergency_contact_provided": assessment.emergency_contact_provided
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Resource endpoints
@app.get("/sessions/{session_id}/resources", response_model=List[Dict[str, Any]])
async def get_resources(
    session_id: str,
    request: ResourceRequest,
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Get resources for a session."""
    try:
        resources = await orch.get_resources(
            session_id=session_id,
            categories=request.categories
        )
        return resources
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Escalation endpoint
@app.post("/sessions/{session_id}/escalate", response_model=Dict[str, Any])
async def initiate_escalation(
    session_id: str,
    request: EscalationRequest,
    orch: PsyAssistOrchestrator = Depends(get_orchestrator)
):
    """Initiate escalation to human support."""
    try:
        result = await orch.initiate_escalation(session_id, request.resource_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return {"error": "Not found", "detail": str(exc)}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return {"error": "Internal server error", "detail": str(exc)}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to PsyAssist AI",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }
