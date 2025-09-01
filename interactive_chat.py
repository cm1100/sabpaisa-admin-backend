#!/usr/bin/env python3
"""
Interactive AI Chat Session
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')
django.setup()

from ai_chat.bedrock_agent import BedrockAgent
from ai_chat.models import AIChatSession
from authentication.models import AdminUser
import getpass

def interactive_chat():
    """Interactive chat session"""
    print("="*60)
    print("🤖 SabPaisa AI Chat Assistant")
    print("="*60)
    
    # Get user
    username = input("Enter username (default: admin@sabpaisa.com): ").strip() or "admin@sabpaisa.com"
    
    try:
        user = AdminUser.objects.get(username=username)
        print(f"✅ Logged in as: {user.username} (Role: {user.groups.first().name if user.groups.exists() else 'admin'})")
    except AdminUser.DoesNotExist:
        print(f"❌ User not found: {username}")
        return
    
    # Create session
    session = AIChatSession.objects.create(user=user)
    print(f"📝 Session ID: {session.session_id}")
    print("-"*60)
    
    # Initialize agent
    agent = BedrockAgent(user=user)
    
    print("\n💬 Start chatting! (Type 'exit' to quit, 'clear' to clear session)")
    print("-"*60)
    
    while True:
        try:
            # Get user input
            message = input("\n👤 You: ").strip()
            
            if message.lower() == 'exit':
                print("\n👋 Goodbye!")
                break
            
            if message.lower() == 'clear':
                session.messages.all().delete()
                print("🗑️ Session cleared")
                continue
            
            if not message:
                continue
            
            # Get AI response
            print("\n🤔 Thinking...")
            response = agent.chat(message, session)
            
            # Display response
            print(f"\n🤖 AI: {response['response']}")
            
            # Show metadata if interesting
            if response.get('tool_calls'):
                print(f"\n🔧 Tools used: {response['tool_calls']}")
            
            if response.get('metadata', {}).get('execution_time_ms'):
                print(f"⏱️ Response time: {response['metadata']['execution_time_ms']}ms")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    # Show session summary
    print("\n" + "="*60)
    print("📊 Session Summary:")
    print(f"- Messages: {session.messages.count()}")
    print(f"- Actions: {session.action_audits.count()}")
    print(f"- Duration: {(session.last_activity - session.created_at).total_seconds():.1f} seconds")
    print("="*60)

if __name__ == "__main__":
    interactive_chat()