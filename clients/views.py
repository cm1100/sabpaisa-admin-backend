"""
Client API Views - Following SOLID Principles
Dependency Inversion: Views depend on service interfaces, not implementations
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.core.files.storage import default_storage
from django.http import HttpResponse
import csv
import json
from io import StringIO
from .models import ClientDataTable
from .services import ClientService
from .serializers import (
    ClientListSerializer, ClientDetailSerializer,
    ClientCreateSerializer, ClientUpdateSerializer,
    ClientBulkOperationSerializer, ClientCloneSerializer,
    ClientStatisticsSerializer
)
from .document_models import ClientDocument
from .document_serializers import (
    ClientDocumentSerializer,
    DocumentUploadSerializer,
    DocumentVerificationSerializer
)
from core.bulk_views import BulkOperationMixin


class ClientViewSet(BulkOperationMixin, viewsets.ModelViewSet):
    """
    Client API ViewSet
    Single Responsibility: Only handles HTTP request/response
    Open/Closed: Can be extended with new actions without modification
    """
    queryset = ClientDataTable.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'client_id'  # Use client_id instead of pk
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = ClientService()  # Dependency Injection
    
    def get_serializer_class(self):
        """
        Interface Segregation: Different serializers for different operations
        """
        if self.action == 'list':
            return ClientListSerializer
        elif self.action == 'create':
            return ClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClientUpdateSerializer
        elif self.action == 'bulk_operation':
            return ClientBulkOperationSerializer
        elif self.action == 'clone':
            return ClientCloneSerializer
        elif self.action == 'statistics':
            return ClientStatisticsSerializer
        return ClientDetailSerializer
    
    def list(self, request):
        """
        List clients with filtering and pagination
        Single Responsibility: Only handles list logic
        """
        filters = {}
        
        # Apply filters from query params
        if 'active' in request.query_params:
            filters['active'] = request.query_params['active'].lower() == 'true'
        if 'client_type' in request.query_params:
            filters['client_type'] = request.query_params['client_type']
        if 'risk_category' in request.query_params:
            filters['risk_category'] = int(request.query_params['risk_category'])
        
        # Search functionality
        search_query = request.query_params.get('search', '')
        if search_query:
            # Search in multiple fields
            from django.db.models import Q
            queryset = self.queryset.filter(
                Q(client_code__icontains=search_query) |
                Q(client_name__icontains=search_query) |
                Q(client_email__icontains=search_query) |
                Q(client_contact__icontains=search_query)
            )
        else:
            queryset = self.queryset
        
        # Apply additional filters
        for key, value in filters.items():
            queryset = queryset.filter(**{key: value})
        
        # Order by creation date
        queryset = queryset.order_by('-creation_date')
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Create new client
        Liskov Substitution: Can be replaced with any viewset implementation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                client = self.service.create(
                    serializer.validated_data,
                    user=request.user if request.user.is_authenticated else None
                )
            
            response_serializer = ClientDetailSerializer(client)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, client_id=None):
        """Get single client details"""
        client = self.service.get(client_id)
        if not client:
            return Response(
                {'error': 'Client not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(client)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update client following REST framework patterns"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Use service layer for business logic
        try:
            with transaction.atomic():
                updated_client = self.service.update(
                    instance.client_id,
                    serializer.validated_data,
                    user=request.user if request.user.is_authenticated else None
                )
                
                if not updated_client:
                    return Response(
                        {'error': 'Update failed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Return updated data with detail serializer
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
                
            response_serializer = ClientDetailSerializer(updated_client)
            return Response(response_serializer.data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, client_id=None):
        """Delete client"""
        try:
            success = self.service.delete(
                client_id,
                user=request.user if request.user.is_authenticated else None
            )
            
            if not success:
                return Response(
                    {'error': 'Client not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_operation(self, request):
        """
        Bulk operations on multiple clients
        Open/Closed: New bulk operations can be added without modifying existing code
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        client_ids = serializer.validated_data['client_ids']
        operation = serializer.validated_data['operation']
        
        try:
            with transaction.atomic():
                if operation == 'activate':
                    count = self.service.bulk_activate(
                        client_ids,
                        user=request.user if request.user.is_authenticated else None
                    )
                    message = f"Successfully activated {count} clients"
                
                elif operation == 'deactivate':
                    count = self.service.repository.bulk_deactivate(client_ids)
                    message = f"Successfully deactivated {count} clients"
                
                else:
                    return Response(
                        {'error': 'Invalid operation'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return Response({'message': message, 'count': count})
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, client_id=None):
        """Activate single client using service layer"""
        try:
            # Use service layer for business logic
            success = self.service.activate_client(
                client_id,
                user=request.user if request.user.is_authenticated else None
            )
            
            if not success:
                return Response(
                    {'error': 'Client not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({'message': 'Client activated successfully'})
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, client_id=None):
        """Deactivate single client using service layer"""
        try:
            # Use service layer for business logic
            success = self.service.deactivate_client(
                client_id,
                user=request.user if request.user.is_authenticated else None
            )
            
            if not success:
                return Response(
                    {'error': 'Client not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({'message': 'Client deactivated successfully'})
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def clone(self, request):
        """
        Clone client configuration
        Single Responsibility: Only handles cloning endpoint
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                new_client = self.service.clone_client(
                    serializer.validated_data['source_client_id'],
                    serializer.validated_data['new_client_code'],
                    user=request.user if request.user.is_authenticated else None
                )
            
            response_serializer = ClientDetailSerializer(new_client)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get client statistics
        Interface Segregation: Separate endpoint for statistics
        """
        stats = self.service.get_client_statistics()
        serializer = self.get_serializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search clients"""
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.db.models import Q
        clients = self.queryset.filter(
            Q(client_code__icontains=query) |
            Q(client_name__icontains=query) |
            Q(client_email__icontains=query) |
            Q(client_contact__icontains=query)
        ).order_by('-creation_date')
        
        # Paginate results
        page = self.paginate_queryset(clients)
        if page is not None:
            serializer = ClientListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ClientListSerializer(clients, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def onboard(self, request):
        """
        Onboard a new client with complete setup
        Including payment modes, fee configuration, etc.
        """
        serializer = ClientCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Create client with full onboarding
                client = self.service.create(
                    serializer.validated_data,
                    user=request.user if request.user.is_authenticated else None
                )
                
                # Initialize additional configurations
                # Payment modes, fee bearers, etc. are handled in service
                
                # Mark client as active and onboarded
                client.active = True
                client.creation_date = timezone.now()
                client.save(update_fields=['active', 'creation_date'])
                
                response_serializer = ClientDetailSerializer(client)
                return Response({
                    'message': 'Client onboarded successfully',
                    'client': response_serializer.data
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f'Onboarding failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post', 'get'])
    def kyc_verification(self, request, client_id=None):
        """
        KYC verification endpoint
        GET: Get current KYC status
        POST: Update KYC status
        """
        client = self.get_object()
        
        if request.method == 'GET':
            # Return current KYC status (using risk_category as proxy)
            kyc_data = {
                'client_id': client.client_id,
                'client_name': client.client_name,
                'kyc_status': 'VERIFIED' if client.risk_category and client.risk_category <= 2 else 'PENDING',
                'kyc_verified_date': client.creation_date,
                'kyc_documents': [],  # Would fetch from related model
                'risk_category': client.risk_category,
                'verification_required': not client.active or client.risk_category is None
            }
            return Response(kyc_data)
        
        elif request.method == 'POST':
            # Update KYC status
            kyc_status = request.data.get('kyc_status')
            documents = request.data.get('documents', [])
            notes = request.data.get('notes', '')
            
            if kyc_status not in ['PENDING', 'VERIFIED', 'REJECTED', 'EXPIRED']:
                return Response(
                    {'error': 'Invalid KYC status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                with transaction.atomic():
                    # Update client KYC status using risk_category
                    if kyc_status == 'VERIFIED':
                        client.risk_category = 1  # Low risk for verified
                        client.active = True
                    elif kyc_status == 'REJECTED':
                        client.risk_category = 5  # High risk for rejected
                        client.active = False
                    else:
                        client.risk_category = 3  # Medium risk for pending
                    
                    client.update_date = timezone.now()
                    client.update_by = request.user.username if request.user.is_authenticated else 'system'
                    client.save()
                    
                    # Log KYC verification
                    self._log_kyc_verification(client, kyc_status, request.user)
                    
                    return Response({
                        'message': f'KYC status updated to {kyc_status}',
                        'client_id': client.client_id,
                        'kyc_status': kyc_status
                    })
            
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        """
        Bulk upload clients from CSV/Excel file
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension not in ['csv', 'xlsx', 'xls']:
            return Response(
                {'error': 'Invalid file format. Only CSV and Excel files are supported'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Process CSV file
            if file_extension == 'csv':
                decoded_file = uploaded_file.read().decode('utf-8')
                io_string = StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                success_count = 0
                error_count = 0
                errors = []
                
                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            # Map CSV columns to model fields
                            client_data = {
                                'client_code': row.get('client_code', '').strip(),
                                'client_name': row.get('client_name', '').strip(),
                                'client_type': row.get('client_type', 'Business').strip(),
                                'client_email': row.get('email', '').strip(),
                                'client_contact': row.get('contact', '').strip(),
                                'client_address': row.get('address', '').strip(),
                                'risk_category': int(row.get('risk_category', 1)) if row.get('risk_category') else 1,
                                'active': row.get('active', 'true').lower() == 'true'
                            }
                            
                            # Validate required fields
                            if not client_data['client_code'] or not client_data['client_name']:
                                errors.append(f"Row {row_num}: Missing required fields (client_code or client_name)")
                                error_count += 1
                                continue
                            
                            # Check if client already exists
                            if ClientDataTable.objects.filter(client_code=client_data['client_code']).exists():
                                errors.append(f"Row {row_num}: Client code {client_data['client_code']} already exists")
                                error_count += 1
                                continue
                            
                            # Create client
                            self.service.create(client_data, user=request.user if request.user.is_authenticated else None)
                            success_count += 1
                            
                        except Exception as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                            error_count += 1
                
                return Response({
                    'message': 'Bulk upload completed',
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': errors[:10]  # Return first 10 errors
                })
            
            # For Excel files, you would need to install and use pandas or openpyxl
            else:
                return Response(
                    {'error': 'Excel file processing not yet implemented'},
                    status=status.HTTP_501_NOT_IMPLEMENTED
                )
        
        except Exception as e:
            return Response(
                {'error': f'File processing failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _check_kyc_required(self, client):
        """Check if KYC verification is required"""
        # Using risk_category and creation_date as proxy for KYC status
        if client.risk_category is None or client.risk_category > 2:
            return True
        
        if client.creation_date:
            # Check if verification is expired (older than 1 year)
            one_year_ago = timezone.now() - timedelta(days=365)
            return client.creation_date < one_year_ago
        
        return True
    
    def _log_kyc_verification(self, client, status, user):
        """Log KYC verification activity"""
        # This would log to audit table
        pass
    
    @action(detail=True, methods=['get', 'post'], parser_classes=[MultiPartParser, FormParser])
    def documents(self, request, client_id=None):
        """
        GET: List all documents for a client
        POST: Upload a new document for a client
        """
        client = self.get_object()
        
        if request.method == 'GET':
            # Get all documents for this client
            documents = ClientDocument.objects.filter(client_id=client.client_id)
            
            # Filter by status if provided
            status_filter = request.query_params.get('status')
            if status_filter:
                documents = documents.filter(status=status_filter)
            
            # Filter by document type if provided
            doc_type = request.query_params.get('document_type')
            if doc_type:
                documents = documents.filter(document_type=doc_type)
            
            serializer = ClientDocumentSerializer(documents, many=True, context={'request': request})
            return Response({
                'client_id': client.client_id,
                'client_name': client.client_name,
                'documents': serializer.data,
                'total_documents': documents.count(),
                'verified_count': documents.filter(status='VERIFIED').count(),
                'pending_count': documents.filter(status='PENDING').count(),
                'rejected_count': documents.filter(status='REJECTED').count()
            })
        
        elif request.method == 'POST':
            # Upload new document
            upload_serializer = DocumentUploadSerializer(data=request.data)
            
            if not upload_serializer.is_valid():
                return Response(
                    upload_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                # Create document instance
                document = ClientDocument.objects.create(
                    client_id=client.client_id,
                    document_type=upload_serializer.validated_data['document_type'],
                    document_name=upload_serializer.validated_data['document_name'],
                    document_file=upload_serializer.validated_data['document_file'],
                    document_number=upload_serializer.validated_data.get('document_number', ''),
                    issue_date=upload_serializer.validated_data.get('issue_date'),
                    expiry_date=upload_serializer.validated_data.get('expiry_date'),
                    notes=upload_serializer.validated_data.get('notes', ''),
                    uploaded_by=request.user.username if request.user.is_authenticated else 'system',
                    status='PENDING'
                )
                
                # Return created document
                serializer = ClientDocumentSerializer(document, context={'request': request})
                return Response(
                    {
                        'message': 'Document uploaded successfully',
                        'document': serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=True, methods=['get', 'post', 'delete'], url_path='documents/(?P<document_id>[^/.]+)')
    def document_detail(self, request, client_id=None, document_id=None):
        """
        GET: View a specific document
        POST: Verify/Reject a document
        DELETE: Delete a document
        """
        client = self.get_object()
        
        try:
            document = ClientDocument.objects.get(
                document_id=document_id,
                client_id=client.client_id
            )
        except ClientDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            serializer = ClientDocumentSerializer(document, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Verify or reject document
            verification_serializer = DocumentVerificationSerializer(data=request.data)
            
            if not verification_serializer.is_valid():
                return Response(
                    verification_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            verified_by = request.user.username if request.user.is_authenticated else 'system'
            new_status = verification_serializer.validated_data['status']
            
            if new_status == 'VERIFIED':
                document.mark_as_verified(verified_by)
            elif new_status == 'REJECTED':
                document.mark_as_rejected(
                    verified_by,
                    verification_serializer.validated_data.get('rejection_reason', '')
                )
            
            # Update notes if provided
            if verification_serializer.validated_data.get('notes'):
                document.notes = verification_serializer.validated_data['notes']
                document.save()
            
            serializer = ClientDocumentSerializer(document, context={'request': request})
            return Response({
                'message': f'Document {new_status.lower()} successfully',
                'document': serializer.data
            })
        
        elif request.method == 'DELETE':
            # Delete the document file from storage
            if document.document_file:
                try:
                    document.document_file.delete()
                except:
                    pass  # File might not exist
            
            document.delete()
            return Response(
                {'message': 'Document deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export clients data in various formats
        Supports: CSV, Excel formats
        """
        format_type = request.query_params.get('format', 'csv').lower()
        
        if format_type not in ['csv', 'excel']:
            return Response(
                {'error': 'Invalid format. Supported formats: csv, excel'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get all clients
            clients = ClientDataTable.objects.all().order_by('-creation_date')
            
            if format_type == 'csv':
                # Create CSV response
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="clients_export.csv"'
                
                writer = csv.writer(response)
                
                # Write header
                writer.writerow([
                    'Client ID',
                    'Client Code', 
                    'Client Name',
                    'Client Type',
                    'Email',
                    'Contact',
                    'Address',
                    'Active',
                    'Risk Category',
                    'Creation Date',
                    'Created By',
                    'Auth Flag',
                    'Refund Applicable',
                    'Push API Flag'
                ])
                
                # Write data rows
                for client in clients:
                    writer.writerow([
                        client.client_id,
                        client.client_code or '',
                        client.client_name or '',
                        client.client_type or '',
                        client.client_email or '',
                        client.client_contact or '',
                        client.client_address or '',
                        'Yes' if client.active else 'No',
                        client.risk_category or '',
                        client.creation_date.strftime('%Y-%m-%d %H:%M:%S') if client.creation_date else '',
                        client.created_by or '',
                        'Yes' if client.auth_flag else 'No',
                        'Yes' if client.refund_applicable else 'No',
                        'Yes' if client.push_api_flag else 'No'
                    ])
                
                return response
            
            elif format_type == 'excel':
                # For Excel, we'll use CSV format but with .xlsx extension
                # In a real implementation, you'd use libraries like openpyxl
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="clients_export.xlsx"'
                
                # For now, return CSV data (would need openpyxl for proper Excel)
                writer = csv.writer(response)
                writer.writerow([
                    'Client ID', 'Client Code', 'Client Name', 'Client Type',
                    'Email', 'Contact', 'Address', 'Active', 'Risk Category',
                    'Creation Date', 'Created By'
                ])
                
                for client in clients:
                    writer.writerow([
                        client.client_id,
                        client.client_code or '',
                        client.client_name or '',
                        client.client_type or '',
                        client.client_email or '',
                        client.client_contact or '',
                        client.client_address or '',
                        'Yes' if client.active else 'No',
                        client.risk_category or '',
                        client.creation_date.strftime('%Y-%m-%d %H:%M:%S') if client.creation_date else '',
                        client.created_by or ''
                    ])
                
                return response
                
        except Exception as e:
            return Response(
                {'error': f'Export failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def generate_api_key(self, request, client_id=None):
        """
        Generate new API key for client
        """
        import secrets
        import string
        
        client = self.get_object()
        
        try:
            with transaction.atomic():
                # Generate secure random API key
                alphabet = string.ascii_letters + string.digits
                api_key = 'sk_' + ''.join(secrets.choice(alphabet) for _ in range(32))
                auth_iv = ''.join(secrets.choice(alphabet) for _ in range(16))
                
                # Update client with new keys
                client.auth_key = api_key
                client.auth_iv = auth_iv
                client.auth_flag = True
                client.auth_type = 'API_KEY'
                client.update_date = timezone.now()
                client.update_by = request.user.username if request.user.is_authenticated else 'system'
                client.save()
                
                return Response({
                    'message': 'API key generated successfully',
                    'client_id': client.client_id,
                    'auth_key': api_key,
                    'auth_iv': auth_iv,
                    'auth_type': 'API_KEY'
                })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )