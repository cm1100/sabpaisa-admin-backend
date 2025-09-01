from rest_framework import serializers
from .models import ZoneConfig, UserZoneAccess, ClientZoneMapping, ZoneBasedRestrictions
from authentication.models import AdminUser


class ZoneConfigSerializer(serializers.ModelSerializer):
    parent_zone_name = serializers.SerializerMethodField()
    child_zones_count = serializers.SerializerMethodField()
    total_clients = serializers.SerializerMethodField()
    total_users = serializers.SerializerMethodField()

    class Meta:
        model = ZoneConfig
        fields = '__all__'
        read_only_fields = ['zone_id', 'created_at', 'updated_at']

    def get_parent_zone_name(self, obj):
        if obj.parent_zone_id:
            try:
                parent = ZoneConfig.objects.get(zone_id=obj.parent_zone_id)
                return parent.zone_name
            except ZoneConfig.DoesNotExist:
                return None
        return None

    def get_child_zones_count(self, obj):
        return ZoneConfig.objects.filter(parent_zone_id=obj.zone_id).count()

    def get_total_clients(self, obj):
        return ClientZoneMapping.objects.filter(zone_id=obj.zone_id).count()

    def get_total_users(self, obj):
        return UserZoneAccess.objects.filter(zone_id=obj.zone_id, is_active=True).count()

    def validate_parent_zone_id(self, value):
        if value:
            try:
                parent_zone = ZoneConfig.objects.get(zone_id=value)
                # Prevent circular references
                if self.instance and parent_zone.zone_id == self.instance.zone_id:
                    raise serializers.ValidationError("A zone cannot be its own parent")
            except ZoneConfig.DoesNotExist:
                raise serializers.ValidationError("Parent zone does not exist")
        return value

    def validate_zone_code(self, value):
        # Check uniqueness
        queryset = ZoneConfig.objects.filter(zone_code=value)
        if self.instance:
            queryset = queryset.exclude(zone_id=self.instance.zone_id)
        
        if queryset.exists():
            raise serializers.ValidationError("Zone code must be unique")
        
        return value


class UserZoneAccessSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    zone_name = serializers.SerializerMethodField()
    zone_code = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    can_access_now = serializers.SerializerMethodField()

    class Meta:
        model = UserZoneAccess
        fields = '__all__'
        read_only_fields = ['access_id', 'granted_at', 'last_accessed', 'access_count']

    def get_user_name(self, obj):
        try:
            user = AdminUser.objects.get(id=obj.user_id)
            return f"{user.first_name} {user.last_name}".strip() or user.username
        except AdminUser.DoesNotExist:
            return f"User {obj.user_id}"

    def get_zone_name(self, obj):
        try:
            zone = ZoneConfig.objects.get(zone_id=obj.zone_id)
            return zone.zone_name
        except ZoneConfig.DoesNotExist:
            return f"Zone {obj.zone_id}"

    def get_zone_code(self, obj):
        try:
            zone = ZoneConfig.objects.get(zone_id=obj.zone_id)
            return zone.zone_code
        except ZoneConfig.DoesNotExist:
            return None

    def get_can_access_now(self, obj):
        return obj.can_access_at_time() and not obj.is_expired

    def validate(self, data):
        # Check if zone exists
        zone_id = data.get('zone_id')
        if zone_id:
            try:
                ZoneConfig.objects.get(zone_id=zone_id, is_active=True)
            except ZoneConfig.DoesNotExist:
                raise serializers.ValidationError("Zone does not exist or is inactive")
        
        return data


class ClientZoneMappingSerializer(serializers.ModelSerializer):
    zone_name = serializers.SerializerMethodField()
    zone_code = serializers.SerializerMethodField()
    zone_type = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = ClientZoneMapping
        fields = '__all__'
        read_only_fields = ['mapping_id', 'created_at']

    def get_zone_name(self, obj):
        try:
            zone = ZoneConfig.objects.get(zone_id=obj.zone_id)
            return zone.zone_name
        except ZoneConfig.DoesNotExist:
            return f"Zone {obj.zone_id}"

    def get_zone_code(self, obj):
        try:
            zone = ZoneConfig.objects.get(zone_id=obj.zone_id)
            return zone.zone_code
        except ZoneConfig.DoesNotExist:
            return None

    def get_zone_type(self, obj):
        try:
            zone = ZoneConfig.objects.get(zone_id=obj.zone_id)
            return zone.zone_type
        except ZoneConfig.DoesNotExist:
            return None

    def validate(self, data):
        # Check if zone exists
        zone_id = data.get('zone_id')
        if zone_id:
            try:
                ZoneConfig.objects.get(zone_id=zone_id, is_active=True)
            except ZoneConfig.DoesNotExist:
                raise serializers.ValidationError("Zone does not exist or is inactive")
        
        # Ensure effective_from is provided
        if not data.get('effective_from'):
            from django.utils import timezone
            data['effective_from'] = timezone.now()
        
        return data


class ZoneBasedRestrictionsSerializer(serializers.ModelSerializer):
    zone_name = serializers.SerializerMethodField()
    zone_code = serializers.SerializerMethodField()

    class Meta:
        model = ZoneBasedRestrictions
        fields = '__all__'
        read_only_fields = ['restriction_id', 'created_at', 'created_by']

    def get_zone_name(self, obj):
        try:
            zone = ZoneConfig.objects.get(zone_id=obj.zone_id)
            return zone.zone_name
        except ZoneConfig.DoesNotExist:
            return f"Zone {obj.zone_id}"

    def get_zone_code(self, obj):
        try:
            zone = ZoneConfig.objects.get(zone_id=obj.zone_id)
            return zone.zone_code
        except ZoneConfig.DoesNotExist:
            return None

    def validate(self, data):
        # Check if zone exists
        zone_id = data.get('zone_id')
        if zone_id:
            try:
                ZoneConfig.objects.get(zone_id=zone_id, is_active=True)
            except ZoneConfig.DoesNotExist:
                raise serializers.ValidationError("Zone does not exist or is inactive")
        
        return data


class ZoneHierarchySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    client_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = ZoneConfig
        fields = [
            'zone_id', 'zone_name', 'zone_code', 'zone_type', 
            'parent_zone_id', 'parent_name', 'is_active',
            'client_count', 'user_count', 'children'
        ]

    def get_children(self, obj):
        children = ZoneConfig.objects.filter(parent_zone_id=obj.zone_id, is_active=True)
        return ZoneHierarchySerializer(children, many=True).data

    def get_parent_name(self, obj):
        if obj.parent_zone_id:
            try:
                parent = ZoneConfig.objects.get(zone_id=obj.parent_zone_id)
                return parent.zone_name
            except ZoneConfig.DoesNotExist:
                return None
        return None

    def get_client_count(self, obj):
        return ClientZoneMapping.objects.filter(zone_id=obj.zone_id).count()

    def get_user_count(self, obj):
        return UserZoneAccess.objects.filter(zone_id=obj.zone_id, is_active=True).count()


class ZoneStatisticsSerializer(serializers.Serializer):
    """Serializer for zone statistics data"""
    zone_info = serializers.DictField()
    hierarchy = serializers.DictField()
    access = serializers.DictField()
    clients = serializers.DictField()
    activity = serializers.DictField()


class UserZoneSummarySerializer(serializers.Serializer):
    """Serializer for user zone access summary"""
    user_id = serializers.IntegerField()
    total_zones = serializers.IntegerField()
    zones = serializers.ListField()
    access_levels = serializers.ListField()
    expired_count = serializers.IntegerField()


class ZoneAssignmentRequestSerializer(serializers.Serializer):
    """Serializer for zone assignment requests"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False
    )
    client_ids = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=False
    )
    access_level = serializers.ChoiceField(
        choices=UserZoneAccess.ACCESS_LEVELS,
        default='VIEW'
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, data):
        if not data.get('user_ids') and not data.get('client_ids'):
            raise serializers.ValidationError(
                "Either user_ids or client_ids must be provided"
            )
        return data


class ZoneAccessValidationSerializer(serializers.Serializer):
    """Serializer for zone access validation requests"""
    zone_id = serializers.IntegerField()
    resource_type = serializers.ChoiceField(
        choices=ZoneBasedRestrictions.RESOURCE_TYPES
    )
    action = serializers.CharField(max_length=20)
    context = serializers.DictField(required=False, default=dict)

    def validate_action(self, value):
        allowed_actions = ['create', 'read', 'update', 'delete']
        if value.lower() not in allowed_actions:
            raise serializers.ValidationError(
                f"Action must be one of: {', '.join(allowed_actions)}"
            )
        return value.lower()


class BulkAccessUpdateSerializer(serializers.Serializer):
    """Serializer for bulk access updates"""
    access_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    access_level = serializers.ChoiceField(choices=UserZoneAccess.ACCESS_LEVELS)


class ExtendAccessSerializer(serializers.Serializer):
    """Serializer for extending access duration"""
    days = serializers.IntegerField(min_value=1, max_value=365, default=30)