"""
API URL configuration for accounts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', api_views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', api_views.ProfileAPIView.as_view(), name='api-profile'),
    path('api-usage/', api_views.APIUsageAPIView.as_view(), name='api-usage'),
    path('change-password/', api_views.ChangePasswordAPIView.as_view(), name='api-change-password'),
]
