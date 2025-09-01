from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reconciliation', views.ReconciliationViewSet, basename='reconciliation')

urlpatterns = [
    path('', include(router.urls)),
]