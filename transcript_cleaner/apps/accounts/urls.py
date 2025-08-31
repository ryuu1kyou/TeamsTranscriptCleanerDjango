"""
URL configuration for accounts app.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('change-password/', views.change_password, name='change_password'),
    path('api-usage/', views.api_usage, name='api_usage'),
    path('reset-api-cost/', views.reset_api_cost, name='reset_api_cost'),
    
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url=reverse_lazy('accounts:password_reset_done')
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Custom login/logout
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('set-language/', views.set_language_session, name='set_language'),
    
    # Role management API endpoints
    path('api/roles/', views.get_roles, name='get_roles'),
    path('api/roles/create/', views.create_role, name='create_role'),
    path('api/roles/<int:role_id>/update/', views.update_role, name='update_role'),
    path('api/roles/<int:role_id>/delete/', views.delete_role, name='delete_role'),
    path('api/users/<int:user_id>/roles/', views.get_user_roles, name='get_user_roles'),
    path('api/roles/assign/', views.assign_role, name='assign_role'),
    path('api/roles/remove/', views.remove_role, name='remove_role'),
    
    # User management API endpoints
    path('api/users/<int:user_id>/', views.get_user, name='get_user'),
]
