"""
Bulk Operations Service
Handles bulk operations across all modules
"""
import csv
import io
import json
import logging
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

logger = logging.getLogger(__name__)


class BulkOperationService:
    """
    Base service for bulk operations
    """
    
    def __init__(self, model_class, serializer_class):
        self.model_class = model_class
        self.serializer_class = serializer_class
    
    def bulk_create(self, data_list: List[Dict[str, Any]], user: Any = None) -> Dict[str, Any]:
        """
        Bulk create records
        """
        created_records = []
        errors = []
        
        try:
            with transaction.atomic():
                for index, data in enumerate(data_list):
                    try:
                        # Add user if model has created_by field
                        if user and hasattr(self.model_class, 'created_by'):
                            data['created_by'] = user
                        
                        serializer = self.serializer_class(data=data)
                        if serializer.is_valid():
                            instance = serializer.save()
                            created_records.append(instance)
                        else:
                            errors.append({
                                'row': index + 1,
                                'errors': serializer.errors
                            })
                    except Exception as e:
                        errors.append({
                            'row': index + 1,
                            'error': str(e)
                        })
                
                if errors and not created_records:
                    # If all failed, rollback
                    raise ValidationError("All records failed validation")
                
                logger.info(f"Bulk created {len(created_records)} records")
                
                return {
                    'success': True,
                    'created_count': len(created_records),
                    'error_count': len(errors),
                    'errors': errors[:10]  # Return first 10 errors
                }
                
        except Exception as e:
            logger.error(f"Bulk create failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'errors': errors
            }
    
    def bulk_update(self, updates: List[Dict[str, Any]], user: Any = None) -> Dict[str, Any]:
        """
        Bulk update records
        Format: [{'id': <id>, 'field1': value1, ...}, ...]
        """
        updated_records = []
        errors = []
        
        try:
            with transaction.atomic():
                for index, update_data in enumerate(updates):
                    try:
                        # Get the ID field
                        id_field = self.model_class._meta.pk.name
                        record_id = update_data.pop(id_field, None)
                        
                        if not record_id:
                            errors.append({
                                'row': index + 1,
                                'error': f'{id_field} is required'
                            })
                            continue
                        
                        # Get the instance
                        instance = self.model_class.objects.get(**{id_field: record_id})
                        
                        # Add user if model has updated_by field
                        if user and hasattr(instance, 'updated_by'):
                            update_data['updated_by'] = user
                        
                        # Update fields
                        for field, value in update_data.items():
                            if hasattr(instance, field):
                                setattr(instance, field, value)
                        
                        instance.save()
                        updated_records.append(instance)
                        
                    except self.model_class.DoesNotExist:
                        errors.append({
                            'row': index + 1,
                            'error': 'Record not found'
                        })
                    except Exception as e:
                        errors.append({
                            'row': index + 1,
                            'error': str(e)
                        })
                
                logger.info(f"Bulk updated {len(updated_records)} records")
                
                return {
                    'success': True,
                    'updated_count': len(updated_records),
                    'error_count': len(errors),
                    'errors': errors[:10]
                }
                
        except Exception as e:
            logger.error(f"Bulk update failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'errors': errors
            }
    
    def bulk_delete(self, ids: List[Any]) -> Dict[str, Any]:
        """
        Bulk delete records
        """
        try:
            with transaction.atomic():
                # Get the ID field
                id_field = self.model_class._meta.pk.name
                
                # Delete records
                deleted_count, _ = self.model_class.objects.filter(
                    **{f'{id_field}__in': ids}
                ).delete()
                
                logger.info(f"Bulk deleted {deleted_count} records")
                
                return {
                    'success': True,
                    'deleted_count': deleted_count
                }
                
        except Exception as e:
            logger.error(f"Bulk delete failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def bulk_action(self, action: str, ids: List[Any], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform custom bulk action
        """
        try:
            with transaction.atomic():
                # Get the ID field
                id_field = self.model_class._meta.pk.name
                
                # Get records
                records = self.model_class.objects.filter(
                    **{f'{id_field}__in': ids}
                )
                
                affected_count = 0
                
                # Perform action based on type
                if action == 'activate':
                    affected_count = records.update(is_active=True)
                elif action == 'deactivate':
                    affected_count = records.update(is_active=False)
                elif action == 'archive':
                    affected_count = records.update(
                        is_archived=True,
                        archived_at=timezone.now()
                    )
                elif action == 'unarchive':
                    affected_count = records.update(
                        is_archived=False,
                        archived_at=None
                    )
                elif action == 'approve':
                    affected_count = records.update(
                        is_approved=True,
                        approved_at=timezone.now()
                    )
                elif action == 'reject':
                    affected_count = records.update(
                        is_approved=False,
                        rejected_at=timezone.now()
                    )
                else:
                    # Custom action - must be implemented in subclass
                    return self.custom_bulk_action(action, records, params)
                
                logger.info(f"Bulk action '{action}' affected {affected_count} records")
                
                return {
                    'success': True,
                    'action': action,
                    'affected_count': affected_count
                }
                
        except Exception as e:
            logger.error(f"Bulk action '{action}' failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def custom_bulk_action(self, action: str, queryset, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override this method in subclasses for custom actions
        """
        raise NotImplementedError(f"Action '{action}' not implemented")


class CSVBulkOperationService(BulkOperationService):
    """
    Service for CSV-based bulk operations
    """
    
    def import_csv(self, csv_file, user: Any = None, mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Import records from CSV file
        """
        try:
            # Read CSV
            csv_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            
            data_list = []
            for row in csv_reader:
                # Apply field mapping if provided
                if mapping:
                    mapped_row = {}
                    for csv_field, model_field in mapping.items():
                        if csv_field in row:
                            mapped_row[model_field] = row[csv_field]
                    data_list.append(mapped_row)
                else:
                    data_list.append(row)
            
            # Perform bulk create
            return self.bulk_create(data_list, user)
            
        except Exception as e:
            logger.error(f"CSV import failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_csv(self, queryset=None, fields: List[str] = None) -> io.StringIO:
        """
        Export records to CSV
        """
        try:
            # Get queryset if not provided
            if queryset is None:
                queryset = self.model_class.objects.all()
            
            # Get fields to export
            if not fields:
                fields = [f.name for f in self.model_class._meta.fields]
            
            # Create CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            
            # Write data
            for record in queryset:
                row_data = {}
                for field in fields:
                    value = getattr(record, field, '')
                    # Convert complex types to string
                    if hasattr(value, 'isoformat'):  # DateTime
                        value = value.isoformat()
                    elif hasattr(value, 'pk'):  # ForeignKey
                        value = str(value.pk)
                    row_data[field] = value
                writer.writerow(row_data)
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            raise


class JSONBulkOperationService(BulkOperationService):
    """
    Service for JSON-based bulk operations
    """
    
    def import_json(self, json_file, user: Any = None) -> Dict[str, Any]:
        """
        Import records from JSON file
        """
        try:
            # Read JSON
            json_data = json_file.read().decode('utf-8')
            data_list = json.loads(json_data)
            
            if not isinstance(data_list, list):
                data_list = [data_list]
            
            # Perform bulk create
            return self.bulk_create(data_list, user)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {str(e)}")
            return {
                'success': False,
                'error': f'Invalid JSON: {str(e)}'
            }
        except Exception as e:
            logger.error(f"JSON import failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_json(self, queryset=None, fields: List[str] = None) -> str:
        """
        Export records to JSON
        """
        try:
            # Get queryset if not provided
            if queryset is None:
                queryset = self.model_class.objects.all()
            
            # Serialize using the serializer
            serializer = self.serializer_class(queryset, many=True)
            return json.dumps(serializer.data, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            raise


class BulkValidationService:
    """
    Service for validating bulk data before import
    """
    
    @staticmethod
    def validate_csv_structure(csv_file, required_fields: List[str]) -> Dict[str, Any]:
        """
        Validate CSV file structure
        """
        try:
            csv_data = csv_file.read().decode('utf-8')
            csv_file.seek(0)  # Reset file pointer
            
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            headers = csv_reader.fieldnames
            
            # Check required fields
            missing_fields = [f for f in required_fields if f not in headers]
            if missing_fields:
                return {
                    'valid': False,
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Count rows
            row_count = sum(1 for _ in csv_reader)
            
            return {
                'valid': True,
                'headers': headers,
                'row_count': row_count
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def validate_data_types(data_list: List[Dict], field_types: Dict[str, type]) -> Dict[str, Any]:
        """
        Validate data types in bulk data
        """
        errors = []
        
        for index, row in enumerate(data_list):
            row_errors = []
            for field, expected_type in field_types.items():
                if field in row:
                    value = row[field]
                    if value is not None and not isinstance(value, expected_type):
                        try:
                            # Try to convert
                            if expected_type == int:
                                int(value)
                            elif expected_type == float:
                                float(value)
                            elif expected_type == bool:
                                str(value).lower() in ['true', '1', 'yes']
                        except:
                            row_errors.append(f"{field}: expected {expected_type.__name__}")
            
            if row_errors:
                errors.append({
                    'row': index + 1,
                    'errors': row_errors
                })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_unique_constraints(model_class, data_list: List[Dict], unique_fields: List[str]) -> Dict[str, Any]:
        """
        Validate unique constraints
        """
        errors = []
        
        for field in unique_fields:
            values = [row.get(field) for row in data_list if row.get(field)]
            
            # Check for duplicates in data
            duplicates = [v for v in values if values.count(v) > 1]
            if duplicates:
                errors.append(f"Duplicate values found for {field}: {', '.join(set(duplicates))}")
            
            # Check against database
            existing = model_class.objects.filter(**{f'{field}__in': values}).values_list(field, flat=True)
            if existing:
                errors.append(f"Values already exist for {field}: {', '.join(existing[:5])}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }