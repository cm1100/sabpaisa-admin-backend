#!/usr/bin/env python
"""
Test AI Chat functionality
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

def test_bedrock_chat():
    """Test the AI chat system"""
    print("Testing AI Chat with Bedrock...")
    
    # Get a test user
    try:
        user = AdminUser.objects.first()
        if not user:
            print("No users found. Creating test user...")
            user = AdminUser.objects.create_user(
                username='ai_test',
                email='ai@test.com',
                password='test123'
            )
    except Exception as e:
        print(f"Error with user: {e}")
        user = None
    
    # Create agent
    agent = BedrockAgent(user=user)
    
    # Test queries
    test_queries = [
        "Hello, what can you help me with?",
        "Show me today's transactions",
        "What is the total transaction volume today?",
        "How many failed transactions are there?",
        "List all active clients"
    ]
    
    # Create session
    session = None
    if user:
        session = AIChatSession.objects.create(user=user)
        print(f"Created session: {session.session_id}")
    
    # Test each query
    for query in test_queries:
        print(f"\n📝 User: {query}")
        try:
            response = agent.chat(query, session)
            print(f"🤖 AI: {response['response'][:500]}")  # Show first 500 chars
            
            if response.get('tool_calls'):
                print(f"🔧 Tools used: {response['tool_calls']}")
            
            if response.get('metadata'):
                print(f"⏱️ Execution time: {response['metadata'].get('execution_time_ms')}ms")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show session stats
    if session:
        print(f"\n📊 Session Stats:")
        print(f"Messages: {session.messages.count()}")
        print(f"Actions logged: {session.action_audits.count()}")

if __name__ == "__main__":
    test_bedrock_chat()