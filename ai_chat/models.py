"""
AI Chat Models for SabPaisa Admin
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AIChatSession(models.Model):
    """Stores AI chat sessions for users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_chat_sessions')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    thread_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ai_chat_sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['session_id']),
            models.Index(fields=['thread_id']),
        ]
    
    def __str__(self):
        return f"Chat Session {self.session_id} - {self.user.username}"


class AIChatMessage(models.Model):
    """Stores individual messages in chat sessions"""
    MESSAGE_TYPES = (
        ('human', 'Human'),
        ('ai', 'AI'),
        ('system', 'System'),
        ('error', 'Error'),
    )
    
    session = models.ForeignKey(AIChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    tool_calls = models.JSONField(default=list, blank=True)
    token_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'ai_chat_messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['message_type']),
        ]
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class AIActionAudit(models.Model):
    """Audit log for AI actions and tool calls"""
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('error', 'Error'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    )
    
    session = models.ForeignKey(AIChatSession, on_delete=models.CASCADE, related_name='action_audits')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_action_audits')
    action_type = models.CharField(max_length=100)
    tool_name = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_ai_actions')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_action_audit'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['tool_name']),
        ]
    
    def __str__(self):
        return f"{self.tool_name} - {self.status} - {self.user.username}"