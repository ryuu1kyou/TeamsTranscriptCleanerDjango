"""
API views for accounts app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from .serializers import (
    UserSerializer, 
    ProfileSerializer, 
    ChangePasswordSerializer,
    APIUsageSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's data."""
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class ProfileAPIView(APIView):
    """
    API endpoint for user profile management.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """Get user profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile."""
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class APIUsageAPIView(APIView):
    """
    API endpoint for API usage statistics.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """Get API usage statistics."""
        user = request.user
        
        # Calculate monthly usage
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        data = {
            'user': {
                'username': user.username,
                'email': user.email,
                'total_api_cost': float(user.total_api_cost),
                'api_usage_limit': float(user.api_usage_limit),
                'remaining_budget': float(user.remaining_api_budget),
                'budget_percentage_used': float(user.api_budget_percentage_used),
            },
            'monthly_usage': {
                'month': current_month_start.strftime('%Y-%m'),
                'cost': 0.0,
                'job_count': 0
            },
            'job_statistics': {
                'total_jobs': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'pending_jobs': 0
            },
            'recent_jobs': []
        }
        
        return Response(data)
    
    def post(self, request):
        """Reset API cost."""
        user = request.user
        user.reset_api_cost()
        return Response({'message': 'API usage cost has been reset'})


class ChangePasswordAPIView(APIView):
    """
    API endpoint for changing password.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['current_password']):
                return Response(
                    {'current_password': 'Current password is incorrect'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
