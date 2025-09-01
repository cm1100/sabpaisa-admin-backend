"""
Bulk Operation Views
Generic views for bulk operations across all modules
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.http import HttpResponse
import logging

from .bulk_operations import (
    BulkOperationService, CSVBulkOperationService,
    JSONBulkOperationService, BulkValidationService
)

logger = logging.getLogger(__name__)


class BulkOperationMixin:
    """
    Mixin to add bulk operations to ViewSets
    """
    
    def get_bulk_service(self):
        """
        Get bulk operation service instance
        Override this method to use custom service
        """
        return BulkOperationService(
            model_class=self.get_queryset().model,
            serializer_class=self.get_serializer_class()
        )
    
    def get_csv_service(self):
        """Get CSV bulk operation service"""
        return CSVBulkOperationService(
            model_class=self.get_queryset().model,
            serializer_class=self.get_serializer_class()
        )
    
    def get_json_service(self):
        """Get JSON bulk operation service"""
        return JSONBulkOperationService(
            model_class=self.get_queryset().model,
            serializer_class=self.get_serializer_class()
        )
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create records
        """
        data_list = request.data.get('data', [])
        
        if not data_list:
            return Response({
                'error': 'No data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = self.get_bulk_service()
        result = service.bulk_create(data_list, user=request.user)
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['put', 'patch'])
    def bulk_update(self, request):
        """
        Bulk update records
        """
        updates = request.data.get('updates', [])
        
        if not updates:
            return Response({
                'error': 'No updates provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = self.get_bulk_service()
        result = service.bulk_update(updates, user=request.user)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Bulk delete records
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return Response({
                'error': 'No IDs provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = self.get_bulk_service()
        result = service.bulk_delete(ids)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """
        Perform custom bulk action
        """
        action_type = request.data.get('action')
        ids = request.data.get('ids', [])
        params = request.data.get('params', {})
        
        if not action_type or not ids:
            return Response({
                'error': 'action and ids are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = self.get_bulk_service()
        result = service.bulk_action(action_type, ids, params)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """
        Import records from CSV file
        """
        csv_file = request.FILES.get('file')
        mapping = request.data.get('mapping', {})
        
        if not csv_file:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        if not csv_file.name.endswith('.csv'):
            return Response({
                'error': 'File must be CSV format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = self.get_csv_service()
        result = service.import_csv(csv_file, user=request.user, mapping=mapping)
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        Export records to CSV file
        """
        # Apply filters from query params
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get fields to export
        fields = request.query_params.get('fields', '').split(',')
        fields = [f.strip() for f in fields if f.strip()]
        
        service = self.get_csv_service()
        
        try:
            csv_output = service.export_csv(queryset, fields or None)
            
            # Create response
            response = HttpResponse(csv_output.getvalue(), content_type='text/csv')
            model_name = self.get_queryset().model.__name__.lower()
            response['Content-Disposition'] = f'attachment; filename="{model_name}_export.csv"'
            
            return response
            
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def import_json(self, request):
        """
        Import records from JSON file
        """
        json_file = request.FILES.get('file')
        
        if not json_file:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        if not json_file.name.endswith('.json'):
            return Response({
                'error': 'File must be JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = self.get_json_service()
        result = service.import_json(json_file, user=request.user)
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def export_json(self, request):
        """
        Export records to JSON file
        """
        # Apply filters from query params
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get fields to export
        fields = request.query_params.get('fields', '').split(',')
        fields = [f.strip() for f in fields if f.strip()]
        
        service = self.get_json_service()
        
        try:
            json_output = service.export_json(queryset, fields or None)
            
            # Create response
            response = HttpResponse(json_output, content_type='application/json')
            model_name = self.get_queryset().model.__name__.lower()
            response['Content-Disposition'] = f'attachment; filename="{model_name}_export.json"'
            
            return response
            
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def validate_csv(self, request):
        """
        Validate CSV file structure before import
        """
        csv_file = request.FILES.get('file')
        
        if not csv_file:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get required fields (override in subclass)
        required_fields = getattr(self, 'csv_required_fields', [])
        
        result = BulkValidationService.validate_csv_structure(csv_file, required_fields)
        
        if result['valid']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def bulk_template(self, request):
        """
        Get CSV template for bulk import
        """
        format_type = request.query_params.get('format', 'csv')
        
        # Get model fields
        model = self.get_queryset().model
        fields = []
        
        for field in model._meta.fields:
            if not field.auto_created and field.name != 'id':
                field_info = {
                    'name': field.name,
                    'type': field.get_internal_type(),
                    'required': not field.blank and not field.null,
                    'max_length': getattr(field, 'max_length', None)
                }
                
                # Add choices if available
                if hasattr(field, 'choices') and field.choices:
                    field_info['choices'] = [c[0] for c in field.choices]
                
                fields.append(field_info)
        
        if format_type == 'csv':
            # Create CSV template
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([f['name'] for f in fields])
            
            # Write example row
            example_row = []
            for field in fields:
                if field['type'] == 'CharField':
                    example_row.append('Example Text')
                elif field['type'] == 'IntegerField':
                    example_row.append('123')
                elif field['type'] == 'DecimalField':
                    example_row.append('99.99')
                elif field['type'] == 'BooleanField':
                    example_row.append('true')
                elif field['type'] == 'DateTimeField':
                    example_row.append('2024-01-01 00:00:00')
                elif field['type'] == 'DateField':
                    example_row.append('2024-01-01')
                else:
                    example_row.append('')
            
            writer.writerow(example_row)
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            model_name = model.__name__.lower()
            response['Content-Disposition'] = f'attachment; filename="{model_name}_template.csv"'
            
            return response
            
        else:
            # Return field information as JSON
            return Response({
                'model': model.__name__,
                'fields': fields
            }, status=status.HTTP_200_OK)


class BulkEnabledModelViewSet(BulkOperationMixin, ModelViewSet):
    """
    ModelViewSet with bulk operations enabled
    """
    pass