"""
Serializers for KYC Document Management
"""
from rest_framework import serializers
from .document_models import ClientDocument


class ClientDocumentSerializer(serializers.ModelSerializer):
    """Serializer for client KYC documents"""
    
    is_expired = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientDocument
        fields = [
            'document_id',
            'client_id',
            'document_type',
            'document_name',
            'document_file',
            'file_url',
            'file_size',
            'document_number',
            'issue_date',
            'expiry_date',
            'is_expired',
            'status',
            'verified_by',
            'verified_date',
            'rejection_reason',
            'uploaded_by',
            'upload_date',
            'last_updated',
            'notes'
        ]
        read_only_fields = [
            'document_id',
            'file_url',
            'file_size',
            'is_expired',
            'upload_date',
            'last_updated'
        ]
    
    def get_is_expired(self, obj):
        """Check if document is expired"""
        return obj.is_expired()
    
    def get_file_url(self, obj):
        """Get full URL for document file"""
        if obj.document_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document_file.url)
            return obj.document_file.url
        return None
    
    def get_file_size(self, obj):
        """Get file size in bytes"""
        if obj.document_file:
            try:
                return obj.document_file.size
            except:
                return None
        return None


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""
    
    document_type = serializers.ChoiceField(choices=ClientDocument.DOCUMENT_TYPES)
    document_name = serializers.CharField(max_length=255)
    document_file = serializers.FileField()
    document_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_document_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 10MB")
        
        # Check file extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        file_ext = value.name.lower().split('.')[-1]
        if f'.{file_ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value


class DocumentVerificationSerializer(serializers.Serializer):
    """Serializer for document verification"""
    
    status = serializers.ChoiceField(choices=['VERIFIED', 'REJECTED'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate verification data"""
        if data['status'] == 'REJECTED' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a document'
            })
        return data