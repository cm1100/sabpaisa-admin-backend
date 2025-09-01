"""
Serializers for AI Chat
"""
from rest_framework import serializers
from .models import AIChatSession, AIChatMessage, AIActionAudit


class AIChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatMessage
        fields = ['id', 'message_type', 'content', 'timestamp', 'metadata', 'tool_calls', 'token_count']
        read_only_fields = ['id', 'timestamp']


class AIChatSessionSerializer(serializers.ModelSerializer):
    messages = AIChatMessageSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AIChatSession
        fields = ['id', 'session_id', 'thread_id', 'user', 'username', 'created_at', 
                 'last_activity', 'is_active', 'metadata', 'messages']
        read_only_fields = ['id', 'session_id', 'created_at', 'last_activity']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat requests"""
    message = serializers.CharField(required=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    context = serializers.JSONField(required=False, default=dict)
    

class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses"""
    response = serializers.CharField()
    session_id = serializers.UUIDField()
    tool_calls = serializers.JSONField(required=False, default=list)
    metadata = serializers.JSONField(required=False, default=dict)


class AIActionAuditSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AIActionAudit
        fields = ['id', 'session', 'user', 'username', 'action_type', 'tool_name', 
                 'parameters', 'result', 'status', 'error_message', 'execution_time_ms',
                 'requires_approval', 'approved_by', 'approved_at', 'created_at']
        read_only_fields = ['id', 'created_at']