#!/usr/bin/env python3
"""
Enhanced CLI interface for PsyAssist AI.
"""

import asyncio
import sys
import argparse
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

BASE_URL = "http://localhost:8000"

class PsyAssistCLI:
    """Enhanced CLI interface for PsyAssist AI."""
    
    def __init__(self):
        self.session_id = None
        self.user_id = None
    
    def print_banner(self):
        """Print application banner."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    🧠 PsyAssist AI CLI                      ║
║              Emergency Emotional Support System              ║
║                                                              ║
║  Commands:                                                   ║
║    health     - Check system health                          ║
║    status     - Show system status                           ║
║    session    - Start new session                            ║
║    chat       - Interactive chat mode                        ║
║    test       - Run API tests                                ║
║    demo       - Run demo conversation                        ║
║    help       - Show this help                               ║
║    quit       - Exit CLI                                     ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    def check_server(self) -> bool:
        """Check if server is running."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def health_check(self):
        """Check system health."""
        print("🏥 Checking system health...")
        
        if not self.check_server():
            print("❌ Server is not running!")
            print("💡 Start the server with: python run.py")
            return
        
        try:
            response = requests.get(f"{BASE_URL}/health")
            data = response.json()
            print(f"✅ Health: {data['status']}")
            print(f"🔧 Service: {data['service']}")
            print(f"📦 Version: {data['version']}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    def show_status(self):
        """Show system status."""
        print("📊 System Status...")
        
        if not self.check_server():
            print("❌ Server is not running!")
            return
        
        try:
            response = requests.get(f"{BASE_URL}/status")
            data = response.json()
            
            print(f"🟢 Health: {data['system_health']}")
            print(f"📈 Active Sessions: {data['active_sessions']}")
            print(f"📊 Total Sessions: {data['total_sessions']}")
            print(f"📨 Event Queue: {data['event_queue_size']}")
            print(f"⏰ Last Update: {data['timestamp']}")
            
            if self.session_id:
                print(f"🎯 Current Session: {self.session_id}")
                
        except Exception as e:
            print(f"❌ Status check failed: {e}")
    
    def create_session(self, user_id: str = None):
        """Create a new session."""
        print("📝 Creating new session...")
        
        if not self.check_server():
            print("❌ Server is not running!")
            return
        
        if not user_id:
            user_id = input("👤 Enter user ID (or press Enter for auto): ").strip()
            if not user_id:
                user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            payload = {
                "user_id": user_id,
                "metadata": {
                    "location": "UA",
                    "cli_session": True,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            response = requests.post(f"{BASE_URL}/sessions", json=payload)
            data = response.json()
            
            self.session_id = data["session_id"]
            self.user_id = user_id
            
            print(f"✅ Session created!")
            print(f"🆔 Session ID: {self.session_id}")
            print(f"👤 User ID: {self.user_id}")
            print(f"⏰ Expires: {data['expires_at']}")
            
        except Exception as e:
            print(f"❌ Session creation failed: {e}")
    
    def send_message(self, message: str):
        """Send a message to current session."""
        if not self.session_id:
            print("❌ No active session! Create one first with 'session'")
            return
        
        try:
            payload = {"message": message}
            response = requests.post(
                f"{BASE_URL}/sessions/{self.session_id}/messages",
                json=payload
            )
            data = response.json()
            
            print(f"🤖 {data['agent']}: {data['content']}")
            
        except Exception as e:
            print(f"❌ Message failed: {e}")
    
    def interactive_chat(self):
        """Start interactive chat mode."""
        if not self.session_id:
            print("📝 Creating session for chat...")
            self.create_session()
        
        if not self.session_id:
            print("❌ Failed to create session!")
            return
        
        print("\n💬 Interactive Chat Mode")
        print("=" * 40)
        print("Type your messages. Commands:")
        print("  /status  - Show session status")
        print("  /risk    - Assess risk of last message")
        print("  /quit    - Exit chat mode")
        print("  /help    - Show this help")
        print()
        
        # Send initial message
        self.send_message("Привіт, я хочу почати розмову")
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    self.handle_chat_command(user_input)
                    continue
                
                self.send_message(user_input)
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Chat interrupted")
                break
            except EOFError:
                break
    
    def handle_chat_command(self, command: str):
        """Handle chat commands."""
        cmd = command.lower()
        
        if cmd == '/quit':
            print("👋 Exiting chat mode...")
            return
        
        elif cmd == '/help':
            print("💬 Chat Commands:")
            print("  /status  - Show session status")
            print("  /risk    - Assess risk of last message")
            print("  /quit    - Exit chat mode")
            print("  /help    - Show this help")
        
        elif cmd == '/status':
            self.show_session_status()
        
        elif cmd == '/risk':
            self.assess_risk()
        
        else:
            print(f"❓ Unknown command: {command}")
    
    def show_session_status(self):
        """Show current session status."""
        if not self.session_id:
            print("❌ No active session!")
            return
        
        try:
            response = requests.get(f"{BASE_URL}/sessions/{self.session_id}")
            data = response.json()
            
            print(f"📊 Session Status:")
            print(f"   State: {data['state']}")
            print(f"   Messages: {data['message_count']}")
            print(f"   Created: {data['created_at']}")
            print(f"   Updated: {data['updated_at']}")
            
        except Exception as e:
            print(f"❌ Status check failed: {e}")
    
    def assess_risk(self):
        """Assess risk of a message."""
        if not self.session_id:
            print("❌ No active session!")
            return
        
        message = input("📝 Enter text to assess risk: ").strip()
        if not message:
            print("❌ No message provided!")
            return
        
        try:
            payload = {"text": message}
            response = requests.post(
                f"{BASE_URL}/sessions/{self.session_id}/risk-assessment",
                json=payload
            )
            data = response.json()
            
            print(f"⚠️ Risk Assessment:")
            print(f"   Severity: {data['overall_severity']}")
            print(f"   Confidence: {data['overall_confidence']:.2f}")
            print(f"   Escalation: {data['escalation_triggered']}")
            
        except Exception as e:
            print(f"❌ Risk assessment failed: {e}")
    
    def run_demo(self):
        """Run demo conversation."""
        print("🎭 PsyAssist AI Demo")
        print("=" * 40)
        
        # Create demo session
        self.create_session("demo_user")
        
        if not self.session_id:
            print("❌ Failed to create demo session!")
            return
        
        # Demo conversation flow
        demo_messages = [
            "Привіт, мені потрібна допомога",
            "Так, я згоден продовжити",
            "Я почуваюся дуже сумно останнім часом",
            "У мене проблеми зі сном",
            "Дякую за допомогу"
        ]
        
        for i, message in enumerate(demo_messages, 1):
            print(f"\n{i}. 👤 Demo User: {message}")
            self.send_message(message)
            print()
            
            if i < len(demo_messages):
                input("Press Enter to continue...")
        
        print("🎉 Demo completed!")
    
    def run_tests(self):
        """Run API tests."""
        print("🧪 Running API tests...")
        
        try:
            # Import and run test
            from test_simple import main as test_main
            return test_main()
        except ImportError:
            print("❌ Test module not found!")
            return 1
    
    def interactive_menu(self):
        """Run interactive menu."""
        self.print_banner()
        
        while True:
            try:
                command = input("\n🔧 PsyAssist> ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif command in ['help', 'h', '?']:
                    self.print_banner()
                
                elif command == 'health':
                    self.health_check()
                
                elif command == 'status':
                    self.show_status()
                
                elif command == 'session':
                    self.create_session()
                
                elif command == 'chat':
                    self.interactive_chat()
                
                elif command == 'demo':
                    self.run_demo()
                
                elif command == 'test':
                    self.run_tests()
                
                elif command == '':
                    continue
                
                else:
                    print(f"❓ Unknown command: {command}")
                    print("💡 Type 'help' for available commands")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                break

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PsyAssist AI Enhanced CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('--user-id', help='User ID for session')
    parser.add_argument('--message', help='Message to send')
    
    args = parser.parse_args()
    
    cli = PsyAssistCLI()
    
    # Check if server is running
    if not cli.check_server():
        print("❌ Server is not running!")
        print("💡 Start the server with: python run.py")
        return 1
    
    # Run specific command or interactive mode
    if args.command:
        if args.command == 'health':
            cli.health_check()
        elif args.command == 'status':
            cli.show_status()
        elif args.command == 'session':
            cli.create_session(args.user_id)
        elif args.command == 'chat':
            cli.interactive_chat()
        elif args.command == 'demo':
            cli.run_demo()
        elif args.command == 'test':
            return cli.run_tests()
        else:
            print(f"❓ Unknown command: {args.command}")
            return 1
    else:
        cli.interactive_menu()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
