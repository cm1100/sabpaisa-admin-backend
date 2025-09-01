"""
AWS Bedrock AI Agent for SabPaisa Admin
Integrates with existing Django REST APIs
"""
import json
import time
import boto3
import requests
from typing import Dict, List, Any, Optional
from django.conf import settings
from .models import AIChatSession, AIChatMessage, AIActionAudit
from botocore.exceptions import ClientError
from time import sleep
import random


class BedrockAgent:
    """AI Agent using AWS Bedrock Claude 3.5 Sonnet"""
    
    def __init__(self, user=None):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name='ap-south-1'  # Mumbai region
        )
        # Using Amazon Nova Pro via APAC cross-region inference profile
        self.model_id = 'apac.amazon.nova-pro-v1:0'
        self.user = user
        self.base_url = "http://localhost:8000/api"
        self.jwt_token = self._get_or_create_jwt_token() if user else None  # Your Django API base URL
        
    def _get_or_create_jwt_token(self) -> Optional[str]:
        """Get or create JWT token for the user"""
        if not self.user:
            return None
            
        # Check if token is already stored on user object
        if hasattr(self.user, 'auth_token'):
            return self.user.auth_token
            
        # Use existing JWT service from authentication app
        from authentication.services import JWTService
        
        try:
            jwt_service = JWTService()
            access_token = jwt_service.generate_access_token(self.user)
            # Store for reuse during this session
            self.user.auth_token = access_token
            return access_token
        except Exception as e:
            print(f"Error generating JWT token: {e}")
            return None
    
    def get_system_prompt(self) -> str:
        """System prompt that defines the AI assistant's role and capabilities"""
        return """You are an AI assistant for SabPaisa Admin System, a payment aggregator platform.
        
Your capabilities include:
1. Transaction Management - Query, search, and analyze payment transactions
2. Client Management - Access and manage client information
3. Settlement Processing - Handle settlement operations
4. Dashboard Analytics - Provide insights on payment metrics
5. Compliance Monitoring - Check KYC status and compliance issues

Available API endpoints you can call:
- GET /api/transactions/ - Get transaction list with filters
- GET /api/clients/ - Get client list
- GET /api/dashboard/metrics/ - Get dashboard metrics
- GET /api/settlements/ - Get settlement information

When users ask questions, analyze their intent and use the appropriate API calls to fetch real data.
Always provide accurate information based on actual API responses.

User Role: {role}
Permissions: {permissions}
""".format(
            role=self.user.groups.first().name if self.user and self.user.groups.exists() else "viewer",
            permissions=self._get_user_permissions()
        )
    
    def _get_user_permissions(self) -> str:
        """Get user's permissions for context"""
        if not self.user:
            return "Read-only access"
        
        if self.user.is_superuser:
            return "Full admin access - all operations allowed"
        
        # Check user's role
        if self.user.groups.filter(name='operations_manager').exists():
            return "Operations access - transactions, settlements, refunds"
        elif self.user.groups.filter(name='configuration_manager').exists():
            return "Configuration access - clients, fees, payment methods"
        elif self.user.groups.filter(name='compliance_officer').exists():
            return "Compliance access - KYC, audit trails, reports"
        else:
            return "Read-only access"
    
    def _make_api_call(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make API call to Django backend with authentication"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        # Add JWT token for authentication
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        elif self.user and hasattr(self.user, 'auth_token'):
            headers['Authorization'] = f'Bearer {self.user.auth_token}'
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API call error: {e}")
            return {"error": str(e)}
    
    def _parse_user_intent(self, message: str) -> Dict:
        """Parse user intent to determine which API to call"""
        message_lower = message.lower()
        
        # Transaction queries
        if any(word in message_lower for word in ['transaction', 'payment', 'txn']):
            if 'failed' in message_lower:
                return {
                    "intent": "query_transactions",
                    "filters": {"status": "FAILED"}
                }
            elif 'today' in message_lower:
                return {
                    "intent": "query_transactions",
                    "filters": {"date": "today"}
                }
            else:
                return {"intent": "query_transactions", "filters": {}}
        
        # Client queries
        elif any(word in message_lower for word in ['client', 'customer', 'merchant']):
            return {"intent": "query_clients", "filters": {}}
        
        # Dashboard/metrics queries
        elif any(word in message_lower for word in ['dashboard', 'metrics', 'volume', 'success rate']):
            return {"intent": "get_metrics"}
        
        # Settlement queries
        elif any(word in message_lower for word in ['settlement', 'settle', 'payout']):
            return {"intent": "query_settlements"}
        
        return {"intent": "general_query"}
    
    def _execute_tool_call(self, intent: Dict) -> Dict:
        """Execute API call based on parsed intent"""
        if intent["intent"] == "query_transactions":
            return self._make_api_call("GET", "/transactions/", params=intent.get("filters", {}))
        
        elif intent["intent"] == "query_clients":
            return self._make_api_call("GET", "/clients/", params=intent.get("filters", {}))
        
        elif intent["intent"] == "get_metrics":
            return self._make_api_call("GET", "/dashboard/metrics/")
        
        elif intent["intent"] == "query_settlements":
            return self._make_api_call("GET", "/settlements/", params=intent.get("filters", {}))
        
        return {"message": "I can help with transactions, clients, settlements, and dashboard metrics."}
    
    def _get_fallback_response(self, message: str) -> str:
        """Provide a helpful fallback response when errors occur"""
        message_lower = message.lower()
        
        if 'hello' in message_lower or 'hi' in message_lower:
            return "Hello! I'm here to help with the SabPaisa admin system. How can I assist you today?"
        elif 'transaction' in message_lower:
            return "I can help you with transaction queries. Currently experiencing some technical issues, but I can explain that transactions can be filtered by status (SUCCESS, FAILED, PENDING), date ranges, and client IDs."
        elif 'client' in message_lower:
            return "I can assist with client management. The system tracks client information including IDs, names, contact details, and transaction history."
        elif 'settlement' in message_lower:
            return "Settlement processing involves reconciling transactions and ensuring proper fund distribution. I can help explain the settlement workflow."
        elif 'help' in message_lower or 'what' in message_lower:
            return "I'm the SabPaisa AI assistant. I can help with:\n• Transaction queries and analysis\n• Client management\n• Settlement processing\n• Dashboard analytics\n• Compliance monitoring\n\nWhat would you like to know more about?"
        else:
            return "I'm here to help with the SabPaisa admin system. I can assist with transactions, clients, settlements, and analytics. What specific information are you looking for?"
    
    def chat(self, message: str, session: Optional[AIChatSession] = None, use_bedrock: bool = True) -> Dict:
        """Main chat interface"""
        start_time = time.time()
        
        # Parse user intent
        intent = self._parse_user_intent(message)
        
        # For simple queries, use local responses to avoid API calls
        message_lower = message.lower()
        if not use_bedrock or ('hello' in message_lower or 'hi' in message_lower or 'help' in message_lower):
            return {
                "response": self._get_fallback_response(message),
                "session_id": session.session_id if session else None,
                "tool_calls": [],
                "metadata": {
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "model": "local"
                }
            }
        
        # Execute tool call if needed
        tool_result = None
        if intent["intent"] != "general_query":
            tool_result = self._execute_tool_call(intent)
            
            # Log the action
            if session and self.user:
                AIActionAudit.objects.create(
                    session=session,
                    user=self.user,
                    action_type=intent["intent"],
                    tool_name=f"api_call_{intent['intent']}",
                    parameters=intent.get("filters", {}),
                    result=tool_result,
                    status='success' if not tool_result.get('error') else 'error',
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
        
        # Prepare context for Bedrock
        context = ""
        if tool_result:
            context = f"\nAPI Response Data: {json.dumps(tool_result, indent=2)}\n"
        
        # Prepare request for Amazon Nova Pro using Converse API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"{message}\n{context}"
                    }
                ]
            }
        ]
        
        system = [
            {
                "text": self.get_system_prompt()
            }
        ]
        
        inference_config = {
            "maxTokens": 500,
            "temperature": 0.1
        }
        
        try:
            # Call Bedrock with retry logic for throttling
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Use Converse API for Nova Pro
                    response = self.bedrock_runtime.converse(
                        modelId=self.model_id,
                        messages=messages,
                        system=system,
                        inferenceConfig=inference_config
                    )
                    break  # Success, exit retry loop
                    
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code == 'ThrottlingException' and retry_count < max_retries - 1:
                        # Exponential backoff with jitter
                        wait_time = (2 ** retry_count) + random.uniform(0, 1)
                        print(f"Throttled by Bedrock, waiting {wait_time:.1f}s before retry {retry_count + 1}/{max_retries}")
                        sleep(wait_time)
                        retry_count += 1
                    else:
                        raise  # Re-raise if not throttling or max retries reached
            
            # Parse response from Converse API
            ai_response = response['output']['message']['content'][0]['text']
            
            # Save messages if session exists
            if session:
                # Save user message
                AIChatMessage.objects.create(
                    session=session,
                    message_type='human',
                    content=message,
                    metadata={'intent': intent}
                )
                
                # Save AI response
                AIChatMessage.objects.create(
                    session=session,
                    message_type='ai',
                    content=ai_response,
                    tool_calls=[intent] if intent["intent"] != "general_query" else [],
                    metadata={'tool_result': tool_result} if tool_result else {}
                )
            
            return {
                "response": ai_response,
                "session_id": session.session_id if session else None,
                "tool_calls": [intent] if intent["intent"] != "general_query" else [],
                "metadata": {
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "model": self.model_id
                }
            }
            
        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}"
            print(f"AI Chat Error: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            
            if session:
                AIChatMessage.objects.create(
                    session=session,
                    message_type='error',
                    content=error_msg
                )
            
            # Try to provide a helpful response even on error
            fallback_response = self._get_fallback_response(message)
            
            return {
                "response": fallback_response,
                "error": error_msg,
                "session_id": session.session_id if session else None
            }