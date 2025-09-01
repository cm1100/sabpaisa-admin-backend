from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count
from .models import ZoneConfig, ClientZoneMapping, UserZoneAccess
import logging

logger = logging.getLogger(__name__)


class ZoneAssignmentService:
    """Service for handling zone assignments"""
    
    def auto_assign_client_to_zone(self, client_id, created_by):
        """Auto-assign client to most suitable zone based on business rules"""
        try:
            # Get client location/business info (integrate with client management)
            client_info = self._get_client_info(client_id)
            
            # Find matching zones based on geographic/business criteria
            suitable_zones = self._find_suitable_zones(client_info)
            
            if not suitable_zones.exists():
                logger.warning(f"No suitable zones found for client {client_id}")
                return None
            
            # Select best zone (highest priority, lowest client count)
            best_zone = suitable_zones.first()
            
            # Create mapping
            with transaction.atomic():
                mapping, created = ClientZoneMapping.objects.get_or_create(
                    client_id=client_id,
                    zone_id=best_zone.zone_id,
                    defaults={
                        'is_primary': True,
                        'auto_assigned': True,
                        'assignment_reason': 'Auto-assigned based on geographic/business criteria',
                        'effective_from': timezone.now(),
                        'created_by': created_by
                    }
                )
                
                if created:
                    logger.info(f"Client {client_id} auto-assigned to zone {best_zone.zone_code}")
                    return {
                        'zone_id': best_zone.zone_id,
                        'zone_name': best_zone.zone_name,
                        'zone_code': best_zone.zone_code,
                        'reason': mapping.assignment_reason
                    }
                else:
                    return {
                        'zone_id': best_zone.zone_id,
                        'zone_name': best_zone.zone_name,
                        'zone_code': best_zone.zone_code,
                        'reason': 'Already assigned'
                    }
                    
        except Exception as e:
            logger.error(f"Auto-assignment failed for client {client_id}: {str(e)}")
            return None
    
    def bulk_assign_clients_to_zone(self, client_ids, zone_id, created_by):
        """Bulk assign multiple clients to a zone"""
        try:
            zone = ZoneConfig.objects.get(zone_id=zone_id)
            created_count = 0
            updated_count = 0
            errors = []
            
            with transaction.atomic():
                for client_id in client_ids:
                    try:
                        mapping, created = ClientZoneMapping.objects.get_or_create(
                            client_id=client_id,
                            zone_id=zone_id,
                            defaults={
                                'is_primary': True,
                                'auto_assigned': False,
                                'assignment_reason': 'Bulk manual assignment',
                                'effective_from': timezone.now(),
                                'created_by': created_by
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            # Update existing mapping
                            mapping.is_primary = True
                            mapping.assignment_reason = 'Bulk manual assignment (updated)'
                            mapping.created_by = created_by
                            mapping.save()
                            updated_count += 1
                            
                    except Exception as e:
                        errors.append(f"Client {client_id}: {str(e)}")
                        
            return {
                'zone_name': zone.zone_name,
                'created': created_count,
                'updated': updated_count,
                'errors': errors,
                'total_processed': len(client_ids)
            }
            
        except ZoneConfig.DoesNotExist:
            return {'error': 'Zone not found'}
        except Exception as e:
            logger.error(f"Bulk assignment failed: {str(e)}")
            return {'error': str(e)}
    
    def _get_client_info(self, client_id):
        """Get client information for zone assignment"""
        # This would integrate with your client management system
        # For demo purposes, return some mock data based on client_id
        # In real implementation, you'd query the client database
        
        # Sample client info based on patterns
        if client_id.startswith('SOUTH'):
            return {
                'client_id': client_id,
                'state': 'KA',  # Karnataka
                'city': 'Bangalore',
                'business_type': 'E_COMMERCE',
                'volume_tier': 'HIGH'
            }
        elif client_id.startswith('NORTH'):
            return {
                'client_id': client_id,
                'state': 'DL',  # Delhi
                'city': 'New Delhi',
                'business_type': 'RETAIL',
                'volume_tier': 'MEDIUM'
            }
        else:
            return {
                'client_id': client_id,
                'state': 'MH',  # Maharashtra
                'city': 'Mumbai',
                'business_type': 'E_COMMERCE',
                'volume_tier': 'HIGH'
            }
    
    def _find_suitable_zones(self, client_info):
        """Find zones suitable for client based on criteria"""
        zones = ZoneConfig.objects.filter(is_active=True)
        
        # Filter by geographic criteria
        if client_info.get('state'):
            zones = zones.filter(
                Q(supported_states__contains=[client_info['state']]) |
                Q(supported_states=[])  # Empty means all states
            )
        
        # Filter by business rules
        if client_info.get('business_type'):
            zones = zones.filter(
                Q(business_rules__supported_business_types__contains=[client_info['business_type']]) |
                Q(business_rules__supported_business_types=[]) |  # Empty means all types
                Q(business_rules__supported_business_types__isnull=True)
            )
        
        # Order by priority and current load
        zones = zones.annotate(
            client_count=Count('clientzonemapping')
        ).order_by('client_count', 'zone_name')
        
        return zones


class ZoneValidationService:
    """Service for validating zone-related operations"""
    
    def validate_zone_hierarchy(self, zone_id, parent_zone_id):
        """Validate zone hierarchy doesn't create cycles"""
        if not parent_zone_id:
            return True, None
        
        current_zone_id = parent_zone_id
        visited = set()
        
        while current_zone_id:
            if current_zone_id == zone_id:
                return False, "Circular reference detected in zone hierarchy"
            
            if current_zone_id in visited:
                return False, "Circular reference in parent zone chain"
            
            visited.add(current_zone_id)
            
            try:
                parent_zone = ZoneConfig.objects.get(zone_id=current_zone_id)
                current_zone_id = parent_zone.parent_zone_id
            except ZoneConfig.DoesNotExist:
                break
        
        return True, None
    
    def validate_geographic_overlap(self, zone_id, geographic_config):
        """Check for geographic overlaps with existing zones"""
        if not geographic_config or not geographic_config.get('supported_states'):
            return True, None
        
        new_states = set(geographic_config['supported_states'])
        
        # Check for overlaps with other geographic zones
        overlapping_zones = ZoneConfig.objects.filter(
            zone_type='GEOGRAPHIC',
            is_active=True
        ).exclude(zone_id=zone_id)
        
        conflicts = []
        for zone in overlapping_zones:
            if zone.supported_states:
                existing_states = set(zone.supported_states)
                overlap = new_states.intersection(existing_states)
                if overlap:
                    conflicts.append({
                        'zone': zone.zone_name,
                        'zone_code': zone.zone_code,
                        'overlapping_states': list(overlap)
                    })
        
        if conflicts:
            return False, f"Geographic overlap detected with zones: {conflicts}"
        
        return True, None
    
    def validate_zone_code_uniqueness(self, zone_code, zone_id=None):
        """Check if zone code is unique"""
        query = ZoneConfig.objects.filter(zone_code=zone_code)
        if zone_id:
            query = query.exclude(zone_id=zone_id)
        
        if query.exists():
            return False, f"Zone code '{zone_code}' already exists"
        
        return True, None


class ZoneAnalyticsService:
    """Service for zone analytics and reporting"""
    
    def get_zone_statistics(self, zone_id):
        """Get comprehensive zone statistics"""
        try:
            zone = ZoneConfig.objects.get(zone_id=zone_id)
            
            stats = {
                'zone_info': {
                    'zone_id': zone.zone_id,
                    'zone_name': zone.zone_name,
                    'zone_code': zone.zone_code,
                    'zone_type': zone.zone_type,
                    'is_active': zone.is_active
                },
                'hierarchy': {
                    'parent_zone': zone.parent_zone.zone_name if zone.parent_zone else None,
                    'child_zones_count': zone.child_zones.count(),
                    'total_descendant_zones': len(zone.get_all_child_zones())
                },
                'access': {
                    'total_users': UserZoneAccess.objects.filter(
                        zone_id=zone_id, is_active=True
                    ).count(),
                    'users_by_level': list(UserZoneAccess.objects.filter(
                        zone_id=zone_id, is_active=True
                    ).values('access_level').annotate(count=Count('access_level'))),
                    'expired_access_count': UserZoneAccess.objects.filter(
                        zone_id=zone_id, 
                        expires_at__lt=timezone.now()
                    ).count()
                },
                'clients': {
                    'total_clients': ClientZoneMapping.objects.filter(
                        zone_id=zone_id
                    ).count(),
                    'primary_clients': ClientZoneMapping.objects.filter(
                        zone_id=zone_id, is_primary=True
                    ).count(),
                    'auto_assigned': ClientZoneMapping.objects.filter(
                        zone_id=zone_id, auto_assigned=True
                    ).count()
                },
                'activity': {
                    'recent_access': UserZoneAccess.objects.filter(
                        zone_id=zone_id,
                        last_accessed__gte=timezone.now().replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                    ).count(),
                    'total_access_count': sum(
                        UserZoneAccess.objects.filter(
                            zone_id=zone_id
                        ).values_list('access_count', flat=True)
                    )
                }
            }
            
            return stats
            
        except ZoneConfig.DoesNotExist:
            return {'error': 'Zone not found'}
        except Exception as e:
            logger.error(f"Failed to get zone statistics: {str(e)}")
            return {'error': 'Failed to retrieve statistics'}
    
    def get_user_zone_summary(self, user_id):
        """Get user's zone access summary"""
        try:
            user_access = UserZoneAccess.objects.filter(
                user_id=user_id,
                is_active=True
            ).select_related()
            
            zones = []
            for access in user_access:
                zone = access.zone
                if zone:
                    zones.append({
                        'zone_id': zone.zone_id,
                        'zone_name': zone.zone_name,
                        'zone_code': zone.zone_code,
                        'zone_type': zone.zone_type,
                        'access_level': access.access_level,
                        'granted_at': access.granted_at,
                        'expires_at': access.expires_at,
                        'is_expired': access.is_expired,
                        'can_access_now': access.can_access_at_time(),
                        'access_count': access.access_count,
                        'last_accessed': access.last_accessed
                    })
            
            return {
                'user_id': user_id,
                'total_zones': len(zones),
                'zones': zones,
                'access_levels': list(set([z['access_level'] for z in zones])),
                'expired_count': len([z for z in zones if z['is_expired']])
            }
            
        except Exception as e:
            logger.error(f"Failed to get user zone summary: {str(e)}")
            return {'error': 'Failed to retrieve user summary'}
    
    def get_zone_hierarchy_tree(self, root_zone_id=None):
        """Get hierarchical tree structure of zones"""
        try:
            if root_zone_id:
                root_zones = ZoneConfig.objects.filter(
                    zone_id=root_zone_id,
                    is_active=True
                )
            else:
                root_zones = ZoneConfig.objects.filter(
                    parent_zone_id__isnull=True,
                    is_active=True
                )
            
            def build_tree(zones):
                tree = []
                for zone in zones:
                    node = {
                        'zone_id': zone.zone_id,
                        'zone_name': zone.zone_name,
                        'zone_code': zone.zone_code,
                        'zone_type': zone.zone_type,
                        'is_active': zone.is_active,
                        'client_count': ClientZoneMapping.objects.filter(
                            zone_id=zone.zone_id
                        ).count(),
                        'user_count': UserZoneAccess.objects.filter(
                            zone_id=zone.zone_id,
                            is_active=True
                        ).count(),
                        'children': build_tree(zone.child_zones.filter(is_active=True))
                    }
                    tree.append(node)
                return tree
            
            return build_tree(root_zones)
            
        except Exception as e:
            logger.error(f"Failed to build zone hierarchy: {str(e)}")
            return []