"""
KYC Document Models for Client Verification
"""
from django.db import models
from django.utils import timezone
import os


def client_document_path(instance, filename):
    """Generate upload path for client documents"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create path: documents/client_{id}/kyc/{timestamp}_{filename}
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f'documents/client_{instance.client_id}/kyc/{timestamp}_{filename}'


class ClientDocument(models.Model):
    """
    KYC Document Model for storing client verification documents
    """
    DOCUMENT_TYPES = [
        ('PAN', 'PAN Card'),
        ('AADHAAR', 'Aadhaar Card'),
        ('GST', 'GST Certificate'),
        ('BANK_STATEMENT', 'Bank Statement'),
        ('INCORPORATION', 'Certificate of Incorporation'),
        ('PARTNERSHIP_DEED', 'Partnership Deed'),
        ('TRADE_LICENSE', 'Trade License'),
        ('OTHER', 'Other Document'),
    ]
    
    DOCUMENT_STATUS = [
        ('PENDING', 'Pending Review'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    document_id = models.AutoField(primary_key=True)
    client_id = models.IntegerField(db_index=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to=client_document_path, max_length=500)
    document_number = models.CharField(max_length=100, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='PENDING')
    verified_by = models.CharField(max_length=100, blank=True, null=True)
    verified_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    uploaded_by = models.CharField(max_length=100)
    upload_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'client_documents'
        managed = True  # Let Django manage this table
        verbose_name = 'Client Document'
        verbose_name_plural = 'Client Documents'
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['client_id', 'document_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.document_name} - Client {self.client_id}"
    
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    def mark_as_verified(self, verified_by):
        """Mark document as verified"""
        self.status = 'VERIFIED'
        self.verified_by = verified_by
        self.verified_date = timezone.now()
        self.save()
    
    def mark_as_rejected(self, rejected_by, reason):
        """Mark document as rejected"""
        self.status = 'REJECTED'
        self.verified_by = rejected_by
        self.verified_date = timezone.now()
        self.rejection_reason = reason
        self.save()