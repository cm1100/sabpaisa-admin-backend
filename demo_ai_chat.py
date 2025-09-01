#!/usr/bin/env python3
"""
Demo AI Chat Session
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

def demo_chat():
    """Demo chat session"""
    print("="*70)
    print("🤖 SabPaisa AI Chat Assistant - Demo Session")
    print("="*70)
    
    # Get admin user
    user = AdminUser.objects.filter(username='admin').first()
    if not user:
        user = AdminUser.objects.first()
    
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"✅ User: {user.username} ({user.email})")
    print(f"📋 Role: {user.groups.first().name if user.groups.exists() else 'Super Admin'}")
    
    # Create session
    session = AIChatSession.objects.create(user=user)
    print(f"📝 Session ID: {session.session_id}")
    print("-"*70)
    
    # Initialize agent
    agent = BedrockAgent(user=user)
    
    # Demo conversations
    conversations = [
        "Hello! What can you help me with?",
        "Can you tell me about today's transaction summary?",
        "How many clients are registered in the system?",
        "What types of payment methods are most commonly used?",
        "Are there any compliance issues I should be aware of?"
    ]
    
    print("\n💬 Starting Demo Conversation...")
    print("="*70)
    
    for message in conversations:
        print(f"\n👤 User: {message}")
        print("-"*70)
        
        try:
            # Get AI response
            response = agent.chat(message, session)
            
            # Display response
            ai_response = response.get('response', 'No response')
            # Wrap long responses
            if len(ai_response) > 500:
                ai_response = ai_response[:497] + "..."
            
            print(f"🤖 AI: {ai_response}")
            
            # Show additional info
            if response.get('tool_calls'):
                print(f"\n🔧 Tools Used:")
                for tool in response['tool_calls']:
                    print(f"   - {tool.get('intent', 'unknown')}")
                    if tool.get('filters'):
                        print(f"     Filters: {tool['filters']}")
            
            if response.get('metadata', {}).get('execution_time_ms'):
                print(f"\n⏱️ Response Time: {response['metadata']['execution_time_ms']}ms")
            
            print("-"*70)
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")
            print("-"*70)
    
    # Show session summary
    print("\n" + "="*70)
    print("📊 Session Summary:")
    print(f"  Total Messages: {session.messages.count()}")
    print(f"  AI Actions Logged: {session.action_audits.count()}")
    
    # Show message breakdown
    message_types = {}
    for msg in session.messages.all():
        message_types[msg.message_type] = message_types.get(msg.message_type, 0) + 1
    
    print(f"\n  Message Breakdown:")
    for msg_type, count in message_types.items():
        print(f"    - {msg_type.capitalize()}: {count}")
    
    # Show actions performed
    if session.action_audits.exists():
        print(f"\n  AI Actions Performed:")
        for audit in session.action_audits.all()[:5]:  # Show first 5
            print(f"    - {audit.action_type}: {audit.status}")
            if audit.execution_time_ms:
                print(f"      Time: {audit.execution_time_ms}ms")
    
    print("="*70)
    print("✅ Demo Complete!")

if __name__ == "__main__":
    demo_chat()