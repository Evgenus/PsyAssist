#!/usr/bin/env python3
"""
Command-line interface for PsyAssist AI.
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional

from .core.orchestrator import PsyAssistOrchestrator
from .config.settings import settings


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PsyAssist AI - Emergency emotional support system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  psyassist serve                    # Start the API server
  psyassist test                     # Run basic tests
  psyassist status                   # Show system status
  psyassist demo                     # Run interactive demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start the API server')
    serve_parser.add_argument('--host', default=settings.api_host, help='Host to bind to')
    serve_parser.add_argument('--port', type=int, default=settings.api_port, help='Port to bind to')
    serve_parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('--basic', action='store_true', help='Run basic tests only')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run interactive demo')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'serve':
            return serve_command(args)
        elif args.command == 'test':
            return test_command(args)
        elif args.command == 'status':
            return status_command(args)
        elif args.command == 'demo':
            return demo_command(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def serve_command(args):
    """Start the API server."""
    import uvicorn
    
    print("🚀 Starting PsyAssist AI server...")
    print(f"📊 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔧 Reload: {args.reload}")
    print()
    
    uvicorn.run(
        "psyassist.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=settings.log_level.lower()
    )
    return 0


def test_command(args):
    """Run tests."""
    if args.basic:
        print("🧪 Running basic tests...")
        # Import and run the basic test
        try:
            from test_basic import main as test_main
            return asyncio.run(test_main())
        except ImportError:
            print("❌ Basic test module not found")
            return 1
    else:
        print("🧪 Running full test suite...")
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pytest"], cwd=Path(__file__).parent.parent)
        return result.returncode


async def status_command(args):
    """Show system status."""
    print("📊 PsyAssist AI System Status")
    print("=" * 40)
    
    try:
        orchestrator = PsyAssistOrchestrator()
        status = await orchestrator.get_system_status()
        
        print(f"🟢 System Health: {status['system_health']}")
        print(f"📈 Active Sessions: {status['active_sessions']}")
        print(f"📊 Total Sessions: {status['total_sessions']}")
        print(f"📨 Event Queue Size: {status['event_queue_size']}")
        print(f"⏰ Timestamp: {status['timestamp']}")
        
        # Show configuration
        print("\n🔧 Configuration:")
        print(f"   API Host: {settings.api_host}")
        print(f"   API Port: {settings.api_port}")
        print(f"   Session Timeout: {settings.session_timeout_minutes} minutes")
        print(f"   Max Messages: {settings.max_messages_per_session}")
        print(f"   Escalation Threshold: {settings.escalation_threshold}")
        print(f"   Emergency Threshold: {settings.emergency_threshold}")
        
        return 0
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return 1


def demo_command(args):
    """Run interactive demo."""
    print("🎭 PsyAssist AI Interactive Demo")
    print("=" * 40)
    print("This demo will simulate a conversation with the system.")
    print("Type 'quit' to exit the demo.")
    print()
    
    async def run_demo():
        orchestrator = PsyAssistOrchestrator()
        
        # Create a demo session
        session = await orchestrator.create_session(
            user_id="demo_user",
            metadata={"location": "US", "demo": True}
        )
        
        print(f"✅ Demo session created: {session.session_id}")
        print()
        
        # Initial greeting
        response = await orchestrator.process_message(
            session.session_id,
            "Hello, I need some help"
        )
        print(f"🤖 {response['content']}")
        print()
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                response = await orchestrator.process_message(
                    session.session_id,
                    user_input
                )
                
                print(f"🤖 {response['content']}")
                print()
                
            except KeyboardInterrupt:
                break
        
        # Close the session
        await orchestrator.close_session(session.session_id, "demo_completed")
        print("👋 Demo completed. Thank you!")
    
    return asyncio.run(run_demo())


if __name__ == "__main__":
    sys.exit(main())
