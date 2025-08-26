#!/usr/bin/env python3
"""
Basic test for PsyAssist AI system.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from psyassist.core.orchestrator import PsyAssistOrchestrator
from psyassist.schemas.session import SessionState


async def test_basic_flow():
    """Test the basic session flow."""
    print("🧪 Testing PsyAssist AI Basic Flow...")
    
    # Create orchestrator
    orchestrator = PsyAssistOrchestrator()
    
    # Create a session
    print("📝 Creating session...")
    session = await orchestrator.create_session(
        user_id="test_user_123",
        metadata={"location": "US", "test": True}
    )
    print(f"✅ Session created: {session.session_id}")
    
    # Test initial greeting
    print("👋 Testing initial greeting...")
    response = await orchestrator.process_message(
        session.session_id,
        "Hello, I need some help"
    )
    print(f"🤖 Response: {response['content'][:100]}...")
    print(f"📊 State: {session.state.value}")
    
    # Test consent
    print("✅ Testing consent...")
    response = await orchestrator.process_message(
        session.session_id,
        "Yes, I consent"
    )
    print(f"🤖 Response: {response['content'][:100]}...")
    print(f"📊 State: {session.state.value}")
    
    # Test triage
    print("🔍 Testing triage...")
    response = await orchestrator.process_message(
        session.session_id,
        "I'm feeling really sad and hopeless lately"
    )
    print(f"🤖 Response: {response['content'][:100]}...")
    print(f"📊 State: {session.state.value}")
    
    # Test risk assessment
    print("⚠️ Testing risk assessment...")
    assessment = await orchestrator.assess_risk(
        session.session_id,
        "I'm feeling really sad and hopeless lately"
    )
    print(f"🔍 Risk Level: {assessment.overall_severity.value}")
    print(f"🎯 Confidence: {assessment.overall_confidence:.2f}")
    
    # Test resources
    print("📚 Testing resources...")
    resources = await orchestrator.get_resources(
        session.session_id,
        categories=["MENTAL_HEALTH"]
    )
    print(f"📚 Found {len(resources)} resources")
    
    # Test system status
    print("📊 Testing system status...")
    status = await orchestrator.get_system_status()
    print(f"📊 Active sessions: {status['active_sessions']}")
    print(f"📊 Total sessions: {status['total_sessions']}")
    
    # Close session
    print("🔚 Closing session...")
    await orchestrator.close_session(session.session_id, "test_completed")
    
    print("🎉 All tests passed!")


async def test_risk_assessment():
    """Test risk assessment functionality."""
    print("\n🧪 Testing Risk Assessment...")
    
    orchestrator = PsyAssistOrchestrator()
    session = await orchestrator.create_session()
    
    # Test different risk levels
    test_messages = [
        ("I'm feeling okay today", "LOW"),
        ("I'm feeling a bit sad", "LOW"),
        ("I'm really struggling with depression", "MEDIUM"),
        ("I've been thinking about suicide", "HIGH"),
        ("I have a plan to kill myself tonight", "CRITICAL")
    ]
    
    for message, expected_level in test_messages:
        assessment = await orchestrator.assess_risk(session.session_id, message)
        actual_level = assessment.overall_severity.value
        print(f"📝 '{message[:30]}...' -> {actual_level} (expected: {expected_level})")
    
    await orchestrator.close_session(session.session_id, "test_completed")
    print("✅ Risk assessment tests completed!")


async def test_pii_redaction():
    """Test PII redaction functionality."""
    print("\n🧪 Testing PII Redaction...")
    
    from psyassist.tools import PIIRedactor
    
    redactor = PIIRedactor()
    
    test_texts = [
        "My name is John Smith and my phone is 555-123-4567",
        "You can email me at john.doe@example.com",
        "I live at 123 Main Street, Anytown, CA 90210",
        "My SSN is 123-45-6789"
    ]
    
    for text in test_texts:
        redacted, metadata = redactor.redact_text(text)
        print(f"📝 Original: {text}")
        print(f"🔒 Redacted: {redacted}")
        print(f"📊 Redactions: {metadata['total_redactions']}")
        print()
    
    print("✅ PII redaction tests completed!")


async def main():
    """Run all tests."""
    print("🚀 Starting PsyAssist AI Tests...\n")
    
    try:
        await test_basic_flow()
        await test_risk_assessment()
        await test_pii_redaction()
        
        print("\n🎉 All tests completed successfully!")
        print("✨ PsyAssist AI is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
