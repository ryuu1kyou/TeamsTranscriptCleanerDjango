"""
Views for user account management.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.forms import UserCreationForm
from decimal import Decimal
import json

# REST Framework imports
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .models import User, UserProfile
from ..corrections.models import CorrectionJob


def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        email = request.POST.get('email', '')
        organization = request.POST.get('organization', '')
        
        if form.is_valid() and email:
            user = form.save(commit=False)
            user.email = email
            user.organization = organization
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            login(request, user)
            messages.success(request, 'アカウントが作成されました。')
            return redirect('transcripts:list')
        elif not email:
            messages.error(request, 'メールアドレスを入力してください。')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    """User profile view."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user statistics
    total_transcripts = request.user.transcripts.count()
    total_jobs = request.user.correction_jobs.count()
    successful_jobs = request.user.correction_jobs.filter(status='completed').count()
    
    context = {
        'user': request.user,
        'profile': profile,
        'total_transcripts': total_transcripts,
        'total_jobs': total_jobs,
        'successful_jobs': successful_jobs,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.organization = request.POST.get('organization', '')
        
        # Update API usage limit (if user has permission)
        api_usage_limit = request.POST.get('api_usage_limit')
        if api_usage_limit:
            try:
                limit = Decimal(api_usage_limit)
                if limit >= Decimal('0.01'):
                    request.user.api_usage_limit = limit
            except (ValueError, TypeError):
                messages.error(request, 'API使用制限の値が正しくありません。')
                return render(request, 'accounts/profile_edit.html', {'profile': profile})
        
        request.user.save()
        
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        profile.phone_number = request.POST.get('phone_number', '')
        profile.timezone = request.POST.get('timezone', 'Asia/Tokyo')
        profile.language_preference = request.POST.get('language_preference', 'ja')
        profile.save()
        
        messages.success(request, 'プロフィールが更新されました。')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile_edit.html', {'profile': profile})


@login_required
def api_usage(request):
    """Display API usage statistics."""
    jobs = CorrectionJob.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate monthly usage
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_jobs = jobs.filter(created_at__gte=current_month_start)
    monthly_cost = sum(job.cost for job in monthly_jobs if job.cost)
    
    # Recent jobs (last 10)
    recent_jobs = jobs[:10]
    
    context = {
        'total_cost': request.user.total_api_cost,
        'usage_limit': request.user.api_usage_limit,
        'remaining_budget': request.user.remaining_api_budget,
        'budget_percentage': request.user.api_budget_percentage_used,
        'monthly_cost': monthly_cost,
        'recent_jobs': recent_jobs,
    }
    
    return render(request, 'accounts/api_usage.html', context)


@login_required
def reset_api_cost(request):
    """Reset user's API cost."""
    if request.method == 'POST':
        request.user.reset_api_cost()
        messages.success(request, 'API使用コストがリセットされました。')
        return redirect('accounts:api_usage')
    
    return render(request, 'accounts/reset_api_cost.html')


@method_decorator(csrf_exempt, name='dispatch')
class UserAPIView(View):
    """API view for user operations."""
    
    def get(self, request):
        """Get user information via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        return JsonResponse({
            'id': request.user.pk,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'organization': request.user.organization,
            'total_api_cost': float(request.user.total_api_cost),
            'api_usage_limit': float(request.user.api_usage_limit),
            'remaining_budget': float(request.user.remaining_api_budget),
            'budget_percentage_used': request.user.api_budget_percentage_used,
            'is_verified': request.user.is_verified,
            'created_at': request.user.created_at.isoformat()
        })
    
    def patch(self, request):
        """Update user information via API."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            
            # Update allowed fields
            if 'first_name' in data:
                request.user.first_name = data['first_name']
            if 'last_name' in data:
                request.user.last_name = data['last_name']
            if 'organization' in data:
                request.user.organization = data['organization']
            
            request.user.save()
            
            return JsonResponse({'message': 'User updated successfully'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# API Views for DRF
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    remaining_budget = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    budget_percentage_used = serializers.FloatField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'organization', 'api_usage_limit', 'total_api_cost', 
                 'remaining_budget', 'budget_percentage_used', 'is_verified', 
                 'created_at']
        read_only_fields = ['id', 'username', 'total_api_cost', 'is_verified', 'created_at']


class UserRegistrationAPIView(APIView):
    """API view for user registration."""
    permission_classes = []
    
    def post(self, request):
        data = request.data
        try:
            user = User.objects.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password'),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                organization=data.get('organization', '')
            )
            UserProfile.objects.create(user=user)
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """API view for user profile management."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserAPIView(APIView):
    """API view to get current user information."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ChangePasswordAPIView(APIView):
    """API view for changing password."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not request.user.check_password(old_password):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.set_password(new_password)
        request.user.save()
        return Response({'message': 'Password changed successfully'})