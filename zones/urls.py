from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ZoneConfigViewSet, UserZoneAccessViewSet, 
    ClientZoneMappingViewSet, ZoneBasedRestrictionsViewSet
)

router = DefaultRouter()
router.register(r'configs', ZoneConfigViewSet, basename='zone-configs')
router.register(r'user-access', UserZoneAccessViewSet, basename='user-zone-access')
router.register(r'client-mappings', ClientZoneMappingViewSet, basename='client-zone-mappings')
router.register(r'restrictions', ZoneBasedRestrictionsViewSet, basename='zone-restrictions')

urlpatterns = [
    path('api/zones/', include(router.urls)),
]