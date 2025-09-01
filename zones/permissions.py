from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from .models import UserZoneAccess, ZoneBasedRestrictions, ClientZoneMapping
import logging

logger = logging.getLogger(__name__)


def zone_access_required(zone_field='zone_id', access_level='VIEW', resource_type=None):
    """Decorator to check zone access permissions"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get user and zone information
            user_id = getattr(request.user, 'id', None)
            if not user_id:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            # Extract zone_id from request
            zone_id = None
            if zone_field in kwargs:
                zone_id = kwargs[zone_field]
            elif zone_field in request.GET:
                zone_id = request.GET[zone_field]
            elif hasattr(request, 'data') and zone_field in request.data:
                zone_id = request.data[zone_field]
            
            if not zone_id:
                return JsonResponse({'error': f'Zone identification required ({zone_field})'}, status=400)
            
            # Check user zone access
            try:
                user_access = UserZoneAccess.objects.get(
                    user_id=user_id,
                    zone_id=zone_id,
                    is_active=True
                )
                
                # Check if access is expired
                if user_access.is_expired:
                    return JsonResponse({'error': 'Zone access has expired'}, status=403)
                
                # Check access level
                access_levels = ['VIEW', 'EDIT', 'ADMIN', 'SUPER_ADMIN']
                required_level_index = access_levels.index(access_level)
                user_level_index = access_levels.index(user_access.access_level)
                
                if user_level_index < required_level_index:
                    return JsonResponse({
                        'error': f'Insufficient access level. Required: {access_level}'
                    }, status=403)
                
                # Check time restrictions
                if not user_access.can_access_at_time():
                    return JsonResponse({
                        'error': 'Access not allowed at this time'
                    }, status=403)
                
                # Check IP restrictions
                client_ip = get_client_ip(request)
                if not user_access.can_access_from_ip(client_ip):
                    return JsonResponse({
                        'error': 'Access not allowed from this location'
                    }, status=403)
                
                # Update access tracking
                user_access.last_accessed = timezone.now()
                user_access.access_count += 1
                user_access.save()
                
                # Check resource-specific restrictions
                if resource_type:
                    allowed, error_msg = check_zone_resource_access(
                        zone_id, 
                        resource_type, 
                        request.method, 
                        request
                    )
                    if not allowed:
                        return JsonResponse({'error': error_msg}, status=403)
                
                # Add zone context to request
                request.user_zone_access = user_access
                request.zone_id = zone_id
                
            except UserZoneAccess.DoesNotExist:
                return JsonResponse({
                    'error': 'No access permissions for this zone'
                }, status=403)
            except Exception as e:
                logger.error(f"Zone access check failed: {str(e)}")
                return JsonResponse({'error': 'Access validation failed'}, status=500)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_zone_resource_access(zone_id, resource_type, http_method, request):
    """Check if zone allows access to specific resource"""
    try:
        restriction = ZoneBasedRestrictions.objects.get(
            zone_id=zone_id,
            resource_type=resource_type,
            is_active=True
        )
        
        # Map HTTP methods to actions
        method_action_map = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        
        action = method_action_map.get(http_method.upper(), 'read')
        
        # Build context from request
        context = {}
        if hasattr(request, 'data') and 'amount' in request.data:
            try:
                context['amount'] = float(request.data['amount'])
            except (ValueError, TypeError):
                pass
        elif 'amount' in request.GET:
            try:
                context['amount'] = float(request.GET['amount'])
            except (ValueError, TypeError):
                pass
        
        return restriction.check_action_allowed(action, context)
        
    except ZoneBasedRestrictions.DoesNotExist:
        # No restrictions means access allowed
        return True, None
    except Exception as e:
        logger.error(f"Resource access check failed: {str(e)}")
        return False, "Access validation failed"


class ZoneAccessMixin:
    """Mixin for ViewSets to add zone-based access control"""
    zone_field = 'zone_id'
    required_access_level = 'VIEW'
    resource_type = None
    
    def dispatch(self, request, *args, **kwargs):
        # Apply zone access check
        if hasattr(self, 'action') and self.action in ['list', 'retrieve', 'create', 'update', 'destroy']:
            zone_id = self.get_zone_id(request, *args, **kwargs)
            if zone_id:
                access_allowed, error_msg = self.check_zone_access(request, zone_id)
                if not access_allowed:
                    return Response({'error': error_msg}, status=status.HTTP_403_FORBIDDEN)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_zone_id(self, request, *args, **kwargs):
        """Extract zone ID from request"""
        if self.zone_field in kwargs:
            return kwargs[self.zone_field]
        elif self.zone_field in request.query_params:
            return request.query_params[self.zone_field]
        elif hasattr(request, 'data') and self.zone_field in request.data:
            return request.data[self.zone_field]
        return None
    
    def check_zone_access(self, request, zone_id):
        """Check if user has zone access"""
        user_id = getattr(request.user, 'id', None)
        if not user_id:
            return False, 'Authentication required'
        
        try:
            user_access = UserZoneAccess.objects.get(
                user_id=user_id,
                zone_id=zone_id,
                is_active=True
            )
            
            if user_access.is_expired:
                return False, 'Zone access has expired'
            
            # Check access level
            access_levels = ['VIEW', 'EDIT', 'ADMIN', 'SUPER_ADMIN']
            required_level_index = access_levels.index(self.required_access_level)
            user_level_index = access_levels.index(user_access.access_level)
            
            if user_level_index < required_level_index:
                return False, f'Insufficient access level. Required: {self.required_access_level}'
            
            # Check time and IP restrictions
            if not user_access.can_access_at_time():
                return False, 'Access not allowed at this time'
            
            client_ip = get_client_ip(request)
            if not user_access.can_access_from_ip(client_ip):
                return False, 'Access not allowed from this location'
            
            return True, None
            
        except UserZoneAccess.DoesNotExist:
            return False, 'No access permissions for this zone'
        except Exception as e:
            logger.error(f"Zone access check failed: {str(e)}")
            return False, 'Access validation failed'


def filter_queryset_by_zones(queryset, user_id, zone_field='zone_id'):
    """Filter queryset based on user's zone access"""
    user_zones = UserZoneAccess.objects.filter(
        user_id=user_id,
        is_active=True
    ).values_list('zone_id', flat=True)
    
    filter_kwargs = {f"{zone_field}__in": user_zones}
    return queryset.filter(**filter_kwargs)


def get_user_accessible_zones(user_id, access_level=None):
    """Get list of zones accessible to user"""
    queryset = UserZoneAccess.objects.filter(
        user_id=user_id,
        is_active=True
    )
    
    if access_level:
        access_levels = ['VIEW', 'EDIT', 'ADMIN', 'SUPER_ADMIN']
        if access_level in access_levels:
            level_index = access_levels.index(access_level)
            allowed_levels = access_levels[level_index:]
            queryset = queryset.filter(access_level__in=allowed_levels)
    
    return queryset.values_list('zone_id', flat=True)


def check_zone_permission(user_id, zone_id, action, resource_type=None, context=None):
    """Comprehensive zone permission check"""
    try:
        # Check basic zone access
        user_access = UserZoneAccess.objects.get(
            user_id=user_id,
            zone_id=zone_id,
            is_active=True
        )
        
        if user_access.is_expired:
            return False, 'Zone access has expired'
        
        # Check time restrictions
        if not user_access.can_access_at_time():
            return False, 'Access not allowed at this time'
        
        # Check resource-specific restrictions
        if resource_type:
            try:
                restriction = ZoneBasedRestrictions.objects.get(
                    zone_id=zone_id,
                    resource_type=resource_type,
                    is_active=True
                )
                
                return restriction.check_action_allowed(action, context)
                
            except ZoneBasedRestrictions.DoesNotExist:
                # No restrictions means access allowed
                pass
        
        return True, None
        
    except UserZoneAccess.DoesNotExist:
        return False, 'No access permissions for this zone'
    except Exception as e:
        logger.error(f"Zone permission check failed: {str(e)}")
        return False, 'Permission check failed'