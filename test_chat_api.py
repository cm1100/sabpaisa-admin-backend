#!/usr/bin/env python3
"""
Test AI Chat API
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin@sabpaisa.com"
PASSWORD = "admin123"

def get_token():
    """Login and get JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    else:
        print(f"Login failed: {response.text}")
        return None

def chat_with_ai(token, message, session_id=None):
    """Send message to AI chat"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    
    response = requests.post(
        f"{BASE_URL}/api/ai-chat/sessions/chat/",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Chat failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    """Main test function"""
    print("🚀 Testing AI Chat API...")
    
    # Get token
    print("\n1️⃣ Getting authentication token...")
    token = get_token()
    if not token:
        print("❌ Failed to get token")
        return
    print(f"✅ Token obtained: {token[:50]}...")
    
    # Test messages
    test_messages = [
        "Hello! What can you help me with?",
        "Show me today's transaction summary",
        "How many clients are currently active?",
        "What is the total transaction volume for today?",
        "Are there any failed transactions that need attention?"
    ]
    
    session_id = None
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}️⃣ User: {message}")
        
        response = chat_with_ai(token, message, session_id)
        
        if response:
            print(f"🤖 AI: {response.get('response', 'No response')[:500]}")
            
            # Store session ID for continuity
            if not session_id and response.get('session_id'):
                session_id = response['session_id']
                print(f"📝 Session ID: {session_id}")
            
            # Show tool calls if any
            if response.get('tool_calls'):
                print(f"🔧 Tools used: {response['tool_calls']}")
            
            # Show execution time
            if response.get('metadata'):
                exec_time = response['metadata'].get('execution_time_ms')
                if exec_time:
                    print(f"⏱️ Response time: {exec_time}ms")
        else:
            print("❌ Failed to get response")

if __name__ == "__main__":
    main()