from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import json
from datetime import datetime, time


class ZoneConfig(models.Model):
    """Zone configuration with hierarchy and geographic/business rules"""
    ZONE_TYPES = [
        ('GEOGRAPHIC', 'Geographic'),
        ('BUSINESS_UNIT', 'Business Unit'),
        ('FUNCTIONAL', 'Functional'),
        ('REGULATORY', 'Regulatory'),
        ('TEMPORAL', 'Temporal')
    ]
    
    zone_id = models.AutoField(primary_key=True)
    zone_name = models.CharField(max_length=100)
    zone_code = models.CharField(max_length=20, unique=True)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES)
    parent_zone_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    # Geographic configuration
    geographic_bounds = models.JSONField(null=True, blank=True)  # GeoJSON format
    supported_states = models.JSONField(default=list)  # ["KA", "TN", "AP"]
    supported_cities = models.JSONField(default=list)  # ["Bangalore", "Chennai"]
    
    # Business rules
    business_rules = models.JSONField(default=dict)
    transaction_limits = models.JSONField(default=dict)  # Min/max amounts per zone
    allowed_payment_methods = models.JSONField(default=list)
    
    # Operational settings
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    auto_assign_new_clients = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100)

    class Meta:
        db_table = 'zone_config'

    def __str__(self):
        return f"{self.zone_code} - {self.zone_name}"

    @property
    def child_zones(self):
        return ZoneConfig.objects.filter(parent_zone_id=self.zone_id)

    @property
    def parent_zone(self):
        if self.parent_zone_id:
            try:
                return ZoneConfig.objects.get(zone_id=self.parent_zone_id)
            except ZoneConfig.DoesNotExist:
                return None
        return None

    def get_all_child_zones(self):
        """Recursively get all child zones"""
        children = []
        for child in self.child_zones:
            children.append(child)
            children.extend(child.get_all_child_zones())
        return children

    def has_geographic_overlap(self, other_zone):
        """Check if two geographic zones overlap"""
        if self.zone_type != 'GEOGRAPHIC' or other_zone.zone_type != 'GEOGRAPHIC':
            return False
        
        # Simple overlap check for states/cities
        self_states = set(self.supported_states)
        other_states = set(other_zone.supported_states)
        return bool(self_states.intersection(other_states))


class UserZoneAccess(models.Model):
    """User access permissions to zones with restrictions"""
    ACCESS_LEVELS = [
        ('VIEW', 'View Only'),
        ('EDIT', 'Edit'),
        ('ADMIN', 'Administrator'),
        ('SUPER_ADMIN', 'Super Administrator')
    ]
    
    access_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    zone_id = models.IntegerField()
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVELS)
    
    # Access metadata
    granted_by = models.CharField(max_length=100)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Access restrictions
    time_restrictions = models.JSONField(default=dict)  # Business hours, days of week
    ip_restrictions = models.JSONField(default=list)  # Allowed IP ranges
    location_restrictions = models.JSONField(default=dict)  # Geographic restrictions
    
    # Audit fields
    last_accessed = models.DateTimeField(null=True)
    access_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_zone_access'
        unique_together = ['user_id', 'zone_id']

    @property
    def zone(self):
        try:
            return ZoneConfig.objects.get(zone_id=self.zone_id)
        except ZoneConfig.DoesNotExist:
            return None

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def can_access_at_time(self, check_time=None):
        """Check if user can access zone at given time"""
        if not self.time_restrictions:
            return True
        
        if check_time is None:
            check_time = timezone.now()
        
        # Check day of week
        if 'allowed_days' in self.time_restrictions:
            weekday = check_time.weekday()  # 0=Monday, 6=Sunday
            if weekday not in self.time_restrictions['allowed_days']:
                return False
        
        # Check time range
        if 'allowed_hours' in self.time_restrictions:
            current_time = check_time.time()
            start_time = datetime.strptime(self.time_restrictions['allowed_hours']['start'], '%H:%M:%S').time()
            end_time = datetime.strptime(self.time_restrictions['allowed_hours']['end'], '%H:%M:%S').time()
            
            if not (start_time <= current_time <= end_time):
                return False
        
        return True

    def can_access_from_ip(self, ip_address):
        """Check if user can access from given IP"""
        if not self.ip_restrictions:
            return True
        
        import ipaddress
        try:
            user_ip = ipaddress.ip_address(ip_address)
            
            for allowed_range in self.ip_restrictions:
                if user_ip in ipaddress.ip_network(allowed_range):
                    return True
        except ValueError:
            return False
        
        return False


class ClientZoneMapping(models.Model):
    """Enhanced client-to-zone mapping with business rules"""
    mapping_id = models.AutoField(primary_key=True)
    client_id = models.CharField(max_length=50)
    zone_id = models.IntegerField()
    is_primary = models.BooleanField(default=False)
    
    # Mapping configuration
    auto_assigned = models.BooleanField(default=False)
    assignment_reason = models.CharField(max_length=200, null=True)
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)
    
    # Business rules for this mapping
    transaction_routing_priority = models.IntegerField(default=1)
    settlement_preferences = models.JSONField(default=dict)
    fee_configuration = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)

    class Meta:
        db_table = 'client_zone_mapping'
        unique_together = ['client_id', 'zone_id']

    @property
    def zone(self):
        try:
            return ZoneConfig.objects.get(zone_id=self.zone_id)
        except ZoneConfig.DoesNotExist:
            return None

    @property
    def is_active(self):
        now = timezone.now()
        if self.effective_from > now:
            return False
        if self.effective_until and self.effective_until < now:
            return False
        return True


class ZoneBasedRestrictions(models.Model):
    """Resource-level restrictions per zone"""
    RESOURCE_TYPES = [
        ('TRANSACTION', 'Transactions'),
        ('SETTLEMENT', 'Settlements'),
        ('REFUND', 'Refunds'),
        ('REPORT', 'Reports'),
        ('CLIENT', 'Client Management'),
        ('USER', 'User Management')
    ]
    
    restriction_id = models.AutoField(primary_key=True)
    zone_id = models.IntegerField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    
    # Permission configuration
    allowed_actions = models.JSONField(default=list)  # ["CREATE", "READ", "UPDATE", "DELETE"]
    denied_actions = models.JSONField(default=list)
    
    # Conditional restrictions
    amount_limits = models.JSONField(default=dict)  # {"min": 1, "max": 100000}
    time_restrictions = models.JSONField(default=dict)
    approval_requirements = models.JSONField(default=dict)
    
    # Additional constraints
    additional_conditions = models.JSONField(default=dict)
    error_message = models.CharField(max_length=500, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)

    class Meta:
        db_table = 'zone_based_restrictions'
        unique_together = ['zone_id', 'resource_type']

    @property
    def zone(self):
        try:
            return ZoneConfig.objects.get(zone_id=self.zone_id)
        except ZoneConfig.DoesNotExist:
            return None

    def check_action_allowed(self, action, context=None):
        """Check if an action is allowed based on restrictions"""
        if not self.is_active:
            return True, None
        
        # Check denied actions first
        if action in self.denied_actions:
            return False, self.error_message or f"{action} is not allowed in this zone"
        
        # Check allowed actions (if specified, must be in list)
        if self.allowed_actions and action not in self.allowed_actions:
            return False, self.error_message or f"{action} is not permitted in this zone"
        
        # Check amount limits
        if context and 'amount' in context and self.amount_limits:
            amount = context['amount']
            min_amount = self.amount_limits.get('min')
            max_amount = self.amount_limits.get('max')
            
            if min_amount and amount < min_amount:
                return False, f"Amount must be at least ₹{min_amount}"
            if max_amount and amount > max_amount:
                return False, f"Amount cannot exceed ₹{max_amount}"
        
        # Check time restrictions
        if self.time_restrictions:
            now = timezone.now()
            if 'business_hours_only' in self.time_restrictions:
                if self.time_restrictions['business_hours_only']:
                    if now.weekday() >= 5 or not (9 <= now.hour <= 17):
                        return False, "This action is only allowed during business hours"
        
        return True, None

    def requires_approval(self, action, context=None):
        """Check if action requires additional approval"""
        if not self.approval_requirements:
            return False, None
        
        approval_config = self.approval_requirements.get(action, {})
        if not approval_config:
            return False, None
        
        # Check amount thresholds
        if context and 'amount' in context:
            amount = context['amount']
            threshold = approval_config.get('amount_threshold')
            if threshold and amount > threshold:
                return True, approval_config.get('approver_level', 'ADMIN')
        
        # Always require approval flag
        if approval_config.get('always_required'):
            return True, approval_config.get('approver_level', 'ADMIN')
        
        return False, None


# EXISTING LEGACY TABLES - DO NOT MODIFY
class UserZoneMapper(models.Model):
    """Legacy user zone mapping table - READ ONLY"""
    id = models.IntegerField(primary_key=True)
    emp_email = models.CharField(max_length=150, blank=True, null=True)
    zone_code = models.CharField(max_length=10, blank=True, null=True)
    emp_code = models.CharField(max_length=20, blank=True, null=True)
    mgr_code = models.CharField(max_length=20, blank=True, null=True)
    role_id = models.CharField(max_length=10, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'user_zone_mapper'


class ClientZoneCodeMapper(models.Model):
    """Legacy client zone code mapping table - READ ONLY"""
    id = models.IntegerField(primary_key=True)
    client_code = models.CharField(max_length=10, blank=True, null=True)
    zone_code = models.CharField(max_length=10, blank=True, null=True)
    original_zone_code = models.CharField(max_length=20, blank=True, null=True)
    userloginid = models.CharField(db_column='userLoginId', max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    old_userlogin = models.CharField(db_column='old_userLogin', max_length=75, blank=True, null=True)
    zone_head_name = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'client_zone_code_mapper'
