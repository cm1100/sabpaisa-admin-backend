#!/usr/bin/env python3
"""
AI Chat Queries - Multiple Examples
"""
import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')
django.setup()

from ai_chat.bedrock_agent import BedrockAgent
from ai_chat.models import AIChatSession
from authentication.models import AdminUser

# Get admin user
user = AdminUser.objects.filter(username='admin').first()
if not user:
    user = AdminUser.objects.first()

# Create session
session = AIChatSession.objects.create(user=user)
agent = BedrockAgent(user=user)

def chat(message):
    """Send a message and display response"""
    print(f"\n{'='*80}")
    print(f"💬 USER: {message}")
    print("-"*80)
    
    start_time = time.time()
    
    try:
        response = agent.chat(message, session)
        ai_text = response.get('response', 'No response')
        
        # Display response (truncate if too long)
        if len(ai_text) > 1000:
            print(f"🤖 AI: {ai_text[:997]}...")
        else:
            print(f"🤖 AI: {ai_text}")
        
        # Show tool usage
        if response.get('tool_calls'):
            print(f"\n📍 Intent Detected: {response['tool_calls'][0].get('intent', 'unknown')}")
            filters = response['tool_calls'][0].get('filters', {})
            if filters:
                print(f"   Filters: {filters}")
        
        # Show timing
        elapsed = (time.time() - start_time) * 1000
        print(f"\n⏱️ Response Time: {elapsed:.0f}ms")
        
        return response
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Header
print("\n" + "="*80)
print(" "*25 + "🤖 SABPAISA AI ASSISTANT DEMO")
print("="*80)
print(f"Session ID: {session.session_id}")
print(f"User: {user.username} (Super Admin)")
print("="*80)

# Run multiple queries
queries = [
    # General greeting
    "Hello! What can you do?",
    
    # Transaction queries
    "What's the total transaction volume today?",
    "Show me failed transactions",
    "How many successful transactions did we process today?",
    
    # Client queries  
    "How many clients do we have?",
    "List active clients",
    
    # Settlement queries
    "What's the settlement status?",
    "Are there any pending settlements?",
    
    # Analytics
    "What's our success rate?",
    "Which payment method is most popular?",
    
    # Complex query
    "Give me a complete overview of today's payment processing performance including transaction volume, success rate, failed transactions, and any issues that need attention."
]

# Process each query
for i, query in enumerate(queries, 1):
    print(f"\n🔹 Query {i}/{len(queries)}")
    response = chat(query)
    
    # Small delay between queries
    if i < len(queries):
        time.sleep(1)

# Final summary
print("\n" + "="*80)
print(" "*30 + "📊 SESSION SUMMARY")
print("="*80)
print(f"Total Messages: {session.messages.count()}")
print(f"Human Messages: {session.messages.filter(message_type='human').count()}")
print(f"AI Responses: {session.messages.filter(message_type='ai').count()}")
print(f"Errors: {session.messages.filter(message_type='error').count()}")
print(f"Actions Logged: {session.action_audits.count()}")

# Show action breakdown
action_types = {}
for audit in session.action_audits.all():
    action_types[audit.action_type] = action_types.get(audit.action_type, 0) + 1

if action_types:
    print(f"\nAction Breakdown:")
    for action, count in action_types.items():
        print(f"  • {action}: {count}")

print("="*80)
print("✅ Demo Complete!")