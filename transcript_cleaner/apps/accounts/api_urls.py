"""
API URL configuration for accounts app.
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

app_name = 'accounts_api'

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User management API
    path('register/', views.UserRegistrationAPIView.as_view(), name='register'),
    path('profile/', views.UserProfileAPIView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change_password'),
    
    # User info
    path('me/', views.CurrentUserAPIView.as_view(), name='current_user'),
]