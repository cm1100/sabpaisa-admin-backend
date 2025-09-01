from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'compliance', views.ComplianceViewSet, basename='compliance')

urlpatterns = [
    path('', include(router.urls)),
]