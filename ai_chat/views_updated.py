"""
Updated AI Chat Views with token passing
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import AIChatSession, AIChatMessage, AIActionAudit
from .serializers import (
    AIChatSessionSerializer, 
    AIChatMessageSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    AIActionAuditSerializer
)
from .bedrock_agent import BedrockAgent


class AIChatViewSet(viewsets.ModelViewSet):
    """AI Chat API endpoints"""
    queryset = AIChatSession.objects.all()
    serializer_class = AIChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter sessions by current user"""
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create new chat session for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """Main chat endpoint"""
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        
        # Get or create session
        if session_id:
            session = get_object_or_404(
                AIChatSession, 
                session_id=session_id, 
                user=request.user
            )
        else:
            session = AIChatSession.objects.create(user=request.user)
        
        # Initialize Bedrock agent with user context
        agent = BedrockAgent(user=request.user)
        
        # Pass the JWT token from the request
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            # Store token on user object temporarily
            request.user.auth_token = auth_header.replace('Bearer ', '')
        
        # Get AI response
        response_data = agent.chat(message, session)
        
        # Update session activity
        session.save()  # Updates last_activity
        
        # Return response
        response_serializer = ChatResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)