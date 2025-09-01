from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from authentication.models import AdminUser
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta, datetime
from django.utils import timezone
from rest_framework import serializers

from .models import ZoneConfig, UserZoneAccess, ClientZoneMapping, ZoneBasedRestrictions
from .serializers import (
    ZoneConfigSerializer, UserZoneAccessSerializer, 
    ClientZoneMappingSerializer, ZoneBasedRestrictionsSerializer,
    ZoneHierarchySerializer, ZoneStatisticsSerializer,
    UserZoneSummarySerializer, ZoneAssignmentRequestSerializer,
    ZoneAccessValidationSerializer, BulkAccessUpdateSerializer,
    ExtendAccessSerializer
)
from .permissions import ZoneAccessMixin, filter_queryset_by_zones
from .services import ZoneAssignmentService, ZoneValidationService, ZoneAnalyticsService


class ZoneConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ZoneConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['zone_type', 'is_active', 'parent_zone_id']
    search_fields = ['zone_name', 'zone_code', 'description']
    ordering_fields = ['zone_name', 'created_at']
    ordering = ['zone_name']

    def get_queryset(self):
        queryset = ZoneConfig.objects.all()
        
        # Filter by user's zone access if not super admin
        if not self.request.user.is_superuser:
            queryset = filter_queryset_by_zones(queryset, self.request.user.id)
        
        return queryset

    def perform_create(self, serializer):
        # Validate zone hierarchy
        validation_service = ZoneValidationService()
        
        parent_zone_id = serializer.validated_data.get('parent_zone_id')
        if parent_zone_id:
            is_valid, error_msg = validation_service.validate_zone_hierarchy(
                None, parent_zone_id
            )
            if not is_valid:
                raise serializers.ValidationError({'parent_zone_id': error_msg})
        
        # Validate geographic overlap for geographic zones
        if serializer.validated_data.get('zone_type') == 'GEOGRAPHIC':
            geographic_config = {
                'supported_states': serializer.validated_data.get('supported_states', [])
            }
            is_valid, error_msg = validation_service.validate_geographic_overlap(
                None, geographic_config
            )
            if not is_valid:
                raise serializers.ValidationError({'supported_states': error_msg})
        
        serializer.save(created_by=self.request.user.username)

    def perform_update(self, serializer):
        # Validate zone hierarchy for updates
        validation_service = ZoneValidationService()
        
        parent_zone_id = serializer.validated_data.get('parent_zone_id')
        if parent_zone_id:
            is_valid, error_msg = validation_service.validate_zone_hierarchy(
                serializer.instance.zone_id, parent_zone_id
            )
            if not is_valid:
                raise serializers.ValidationError({'parent_zone_id': error_msg})
        
        serializer.save()

    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """Get zone hierarchy tree"""
        analytics_service = ZoneAnalyticsService()
        
        # Get root zones or specific zone if provided
        root_zone_id = request.query_params.get('root_zone_id')
        
        try:
            hierarchy_data = analytics_service.get_zone_hierarchy_tree(root_zone_id)
            return Response(hierarchy_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to build hierarchy: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def assign_users(self, request, pk=None):
        """Bulk assign users to zone"""
        zone = self.get_object()
        serializer = ZoneAssignmentRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            user_ids = serializer.validated_data.get('user_ids', [])
            access_level = serializer.validated_data.get('access_level', 'VIEW')
            expires_at = serializer.validated_data.get('expires_at')
            
            if not user_ids:
                return Response(
                    {'error': 'user_ids required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            created_count = 0
            errors = []
            
            for user_id in user_ids:
                try:
                    user = AdminUser.objects.get(id=user_id)
                    access, created = UserZoneAccess.objects.get_or_create(
                        user_id=user_id,
                        zone_id=zone.zone_id,
                        defaults={
                            'access_level': access_level,
                            'granted_by': request.user.username,
                            'expires_at': expires_at,
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        # Update existing access
                        access.access_level = access_level
                        access.expires_at = expires_at
                        access.granted_by = request.user.username
                        access.is_active = True
                        access.save()
                        
                except AdminUser.DoesNotExist:
                    errors.append(f"User {user_id} not found")
                except Exception as e:
                    errors.append(f"User {user_id}: {str(e)}")
            
            return Response({
                'message': f'{created_count} users assigned to zone',
                'zone': zone.zone_name,
                'errors': errors
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def assign_clients(self, request, pk=None):
        """Bulk assign clients to zone"""
        zone = self.get_object()
        serializer = ZoneAssignmentRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            client_ids = serializer.validated_data.get('client_ids', [])
            
            if not client_ids:
                return Response(
                    {'error': 'client_ids required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = ZoneAssignmentService()
            result = service.bulk_assign_clients_to_zone(
                client_ids, 
                zone.zone_id, 
                request.user.username
            )
            
            return Response(result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get zone statistics"""
        zone = self.get_object()
        analytics_service = ZoneAnalyticsService()
        
        stats = analytics_service.get_zone_statistics(zone.zone_id)
        
        if 'error' in stats:
            return Response(stats, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = ZoneStatisticsSerializer(stats)
        return Response(serializer.data)


class UserZoneAccessViewSet(viewsets.ModelViewSet):
    serializer_class = UserZoneAccessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['zone_id', 'access_level', 'is_active']
    
    def get_queryset(self):
        queryset = UserZoneAccess.objects.all().order_by('-granted_at')
        
        # Filter by user's manageable zones
        if not self.request.user.is_superuser:
            # Users can only see access records for zones they have ADMIN access to
            admin_zones = UserZoneAccess.objects.filter(
                user_id=self.request.user.id,
                access_level__in=['ADMIN', 'SUPER_ADMIN'],
                is_active=True
            ).values_list('zone_id', flat=True)
            
            queryset = queryset.filter(zone_id__in=admin_zones)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user.username)

    @action(detail=True, methods=['post'])
    def extend_access(self, request, pk=None):
        """Extend user's zone access expiry"""
        access = self.get_object()
        serializer = ExtendAccessSerializer(data=request.data)
        
        if serializer.is_valid():
            days = serializer.validated_data['days']
            
            if access.expires_at:
                new_expiry = access.expires_at + timedelta(days=days)
            else:
                new_expiry = timezone.now() + timedelta(days=days)
            
            access.expires_at = new_expiry
            access.save()
            
            return Response({
                'message': f'Access extended by {days} days',
                'new_expiry': new_expiry.isoformat()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_update_access(self, request):
        """Bulk update user access levels"""
        serializer = BulkAccessUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            access_ids = serializer.validated_data['access_ids']
            new_access_level = serializer.validated_data['access_level']
            
            updated = UserZoneAccess.objects.filter(
                access_id__in=access_ids
            ).update(access_level=new_access_level)
            
            return Response({
                'message': f'{updated} access records updated',
                'new_access_level': new_access_level
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def user_summary(self, request):
        """Get user's zone access summary"""
        user_id = request.query_params.get('user_id', request.user.id)
        
        analytics_service = ZoneAnalyticsService()
        summary = analytics_service.get_user_zone_summary(user_id)
        
        if 'error' in summary:
            return Response(summary, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = UserZoneSummarySerializer(summary)
        return Response(serializer.data)


class ClientZoneMappingViewSet(viewsets.ModelViewSet):
    serializer_class = ClientZoneMappingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client_id', 'zone_id', 'is_primary']

    def get_queryset(self):
        queryset = ClientZoneMapping.objects.all().order_by('-created_at')
        
        # Filter by accessible zones
        if not self.request.user.is_superuser:
            queryset = filter_queryset_by_zones(queryset, self.request.user.id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    @action(detail=False, methods=['post'])
    def auto_assign(self, request):
        """Auto-assign clients to zones based on business rules"""
        client_ids = request.data.get('client_ids', [])
        
        if not client_ids:
            return Response({
                'error': 'client_ids required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = ZoneAssignmentService()
        results = []
        
        for client_id in client_ids:
            result = service.auto_assign_client_to_zone(client_id, request.user.username)
            results.append({
                'client_id': client_id,
                'assigned_zone': result.get('zone_name') if result else None,
                'zone_code': result.get('zone_code') if result else None,
                'reason': result.get('reason') if result else 'No suitable zone found'
            })
        
        return Response({'assignments': results})


class ZoneBasedRestrictionsViewSet(viewsets.ModelViewSet):
    serializer_class = ZoneBasedRestrictionsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['zone_id', 'resource_type', 'is_active']

    def get_queryset(self):
        queryset = ZoneBasedRestrictions.objects.all().order_by('zone_id', 'resource_type')
        
        # Filter by accessible zones
        if not self.request.user.is_superuser:
            queryset = filter_queryset_by_zones(queryset, self.request.user.id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    @action(detail=False, methods=['post'])
    def validate_access(self, request):
        """Validate if an action is allowed in a zone"""
        serializer = ZoneAccessValidationSerializer(data=request.data)
        
        if serializer.is_valid():
            zone_id = serializer.validated_data['zone_id']
            resource_type = serializer.validated_data['resource_type']
            action = serializer.validated_data['action']
            context = serializer.validated_data.get('context', {})
            
            try:
                restriction = ZoneBasedRestrictions.objects.get(
                    zone_id=zone_id,
                    resource_type=resource_type,
                    is_active=True
                )
                
                allowed, message = restriction.check_action_allowed(action, context)
                requires_approval, approver_level = restriction.requires_approval(action, context)
                
                return Response({
                    'allowed': allowed,
                    'message': message,
                    'requires_approval': requires_approval,
                    'approver_level': approver_level
                })
                
            except ZoneBasedRestrictions.DoesNotExist:
                return Response({
                    'allowed': True,
                    'message': 'No restrictions found',
                    'requires_approval': False,
                    'approver_level': None
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
