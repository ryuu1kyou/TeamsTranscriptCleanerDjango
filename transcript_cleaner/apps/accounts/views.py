"""
Views for user account management.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, update_session_auth_hash, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
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
from django.contrib.auth.models import Group
from .forms import (
    CustomUserCreationForm, UserProfileForm, UserProfileExtendedForm, 
    ChangePasswordCustomForm
)
from ..corrections.models import CorrectionJob


class CustomLoginView(LoginView):
    """カスタムログインビュー - 言語設定処理付き"""
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """ログイン成功時の処理"""
        response = super().form_valid(form)
        
        # 言語設定を取得
        language_preference = self.request.POST.get('language_preference', 'ja')
        
        # ユーザープロフィールの言語設定を更新
        try:
            profile = self.request.user.profile
            profile.language_preference = language_preference
            profile.save(update_fields=['language_preference'])
        except UserProfile.DoesNotExist:
            # プロフィールが存在しない場合は作成
            UserProfile.objects.create(
                user=self.request.user,
                language_preference=language_preference
            )
        
        return response


@csrf_exempt
def set_language_session(request):
    """セッションに言語設定を保存"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            language = data.get('language', 'ja')
            
            # セッションに言語設定を保存
            request.session['language_preference'] = language
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'アカウントが作成されました。')
            return redirect('transcripts:list')
    else:
        form = CustomUserCreationForm()
    
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
        user_form = UserProfileForm(request.POST, instance=request.user)
        profile_form = UserProfileExtendedForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'プロフィールが更新されました。')
            return redirect('accounts:profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        profile_form = UserProfileExtendedForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def change_password(request):
    """Change user password."""
    if request.method == 'POST':
        form = ChangePasswordCustomForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'パスワードが変更されました。')
            return redirect('accounts:profile')
    else:
        form = ChangePasswordCustomForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


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


@login_required
def logout_view(request):
    """Handle user logout."""
    from django.contrib.auth import logout
    
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'ログアウトしました。')
        return redirect('accounts:login')
    
    # For GET requests, you might want to show a confirmation page
    # But typically logout is handled via POST for security
    # Redirect to login page
    return redirect('accounts:login')


# ============ Role Management Views ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_roles(request):
    """Get all available roles (groups)."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    groups = Group.objects.all().order_by('name')
    roles = [{'id': group.id, 'name': group.name} for group in groups]
    return Response({'roles': roles})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_role(request):
    """Create a new role (group)."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    name = request.data.get('name', '').strip()
    if not name:
        return Response({'error': 'Role name is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if Group.objects.filter(name=name).exists():
        return Response({'error': 'Role already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    group = Group.objects.create(name=name)
    return Response({'message': 'Role created successfully', 'role': {'id': group.id, 'name': group.name}})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_role(request, role_id):
    """Delete a role (group)."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        group = Group.objects.get(id=role_id)
        # Don't allow deletion of built-in admin roles
        if group.name in ['admin', 'superuser']:
            return Response({'error': 'Cannot delete built-in role'}, status=status.HTTP_400_BAD_REQUEST)
        
        group.delete()
        return Response({'message': 'Role deleted successfully'})
    except Group.DoesNotExist:
        return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_roles(request, user_id):
    """Get roles assigned to a specific user."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        roles = user.get_role_names()
        return Response({'user_id': user_id, 'roles': roles})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_role(request):
    """Assign a role to a user."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    user_id = request.data.get('user_id')
    role_name = request.data.get('role_name')
    
    if not user_id or not role_name:
        return Response({'error': 'user_id and role_name are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id)
        group = Group.objects.get(name=role_name)
        
        if user.has_role(role_name):
            return Response({'error': 'User already has this role'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.groups.add(group)
        return Response({'message': f'Role {role_name} assigned to user successfully'})
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Group.DoesNotExist:
        return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_role(request):
    """Remove a role from a user."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    user_id = request.data.get('user_id')
    role_name = request.data.get('role_name')
    
    if not user_id or not role_name:
        return Response({'error': 'user_id and role_name are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id)
        group = Group.objects.get(name=role_name)
        
        if not user.has_role(role_name):
            return Response({'error': 'User does not have this role'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Don't allow removal of admin role from superuser
        if role_name in ['admin', 'superuser'] and user.is_superuser:
            return Response({'error': 'Cannot remove admin role from superuser'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.groups.remove(group)
        return Response({'message': f'Role {role_name} removed from user successfully'})
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Group.DoesNotExist:
        return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request, user_id):
    """Get user information by ID."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        return Response({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        })
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_role(request, role_id):
    """Update a role name."""
    if not request.user.can_manage_users():
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    new_name = request.data.get('name', '').strip()
    if not new_name:
        return Response({'error': 'Role name is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        group = Group.objects.get(id=role_id)
        
        # Don't allow renaming of built-in admin roles
        if group.name in ['admin', 'superuser']:
            return Response({'error': 'Cannot rename built-in role'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if new name already exists
        if Group.objects.filter(name=new_name).exclude(id=role_id).exists():
            return Response({'error': 'Role name already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_name = group.name
        group.name = new_name
        group.save()
        
        return Response({
            'message': f'Role renamed from {old_name} to {new_name}',
            'role': {'id': group.id, 'name': group.name}
        })
    
    except Group.DoesNotExist:
        return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
