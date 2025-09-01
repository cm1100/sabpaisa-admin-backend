#!/usr/bin/env python3
"""
AI Chat Session - Direct Execution
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')
django.setup()

from ai_chat.bedrock_agent import BedrockAgent
from ai_chat.models import AIChatSession, AIChatMessage
from authentication.models import AdminUser

# Get admin user
user = AdminUser.objects.filter(username='admin').first()
if not user:
    user = AdminUser.objects.first()

print("="*70)
print("🤖 SABPAISA AI CHAT ASSISTANT")
print("="*70)
print(f"👤 User: {user.username} | Role: {user.groups.first().name if user.groups.exists() else 'Super Admin'}")

# Create new session
session = AIChatSession.objects.create(user=user)
print(f"📝 Session: {session.session_id}")
print("="*70)

# Initialize agent
agent = BedrockAgent(user=user)

# Function to process a message
def send_message(message):
    print(f"\n💬 YOU: {message}")
    print("-"*70)
    
    try:
        response = agent.chat(message, session)
        ai_response = response.get('response', 'No response')
        
        print(f"🤖 AI: {ai_response[:800]}")  # Show first 800 chars
        
        if response.get('tool_calls'):
            print(f"\n🔧 Actions Attempted:")
            for tool in response['tool_calls']:
                print(f"  • {tool.get('intent', 'unknown')}")
                if tool.get('filters'):
                    for key, value in tool['filters'].items():
                        print(f"    - {key}: {value}")
        
        if response.get('metadata', {}).get('execution_time_ms'):
            print(f"\n⏱️ Response Time: {response['metadata']['execution_time_ms']}ms")
            
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}")
    
    print("="*70)
    return response

# Start conversation
print("\n🚀 STARTING AI CHAT SESSION...")
print("Type your questions below:\n")

# Example conversation starters
messages = [
    "What capabilities do you have?",
    "Show me a summary of today's transactions",
    "How many clients are in the system?",
    "What payment methods are being used?",
    "Are there any failed transactions I should know about?"
]

print("📌 EXAMPLE QUERIES:")
for i, msg in enumerate(messages, 1):
    print(f"  {i}. {msg}")
print("\n" + "="*70)

# Send first message
response = send_message("Hello! I'm the admin. What's the current status of our payment system?")

# Show session stats
print(f"\n📊 Session Stats: {session.messages.count()} messages, {session.action_audits.count()} actions logged")