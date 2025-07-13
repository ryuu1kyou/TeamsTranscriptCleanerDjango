"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'username', 'get_full_name', 'organization', 
        'api_usage_status', 'is_verified', 'is_staff', 'date_joined'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'is_verified',
        'date_joined', 'last_login'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name', 'organization')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('organization', 'api_usage_limit', 'total_api_cost', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'organization', 'api_usage_limit')
        }),
    )

    def api_usage_status(self, obj):
        """Display API usage status with color coding."""
        percentage = obj.api_budget_percentage_used
        if percentage < 50:
            color = 'green'
        elif percentage < 80:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">${:.2f} / ${:.2f} ({:.1f}%)</span>',
            color, obj.total_api_cost, obj.api_usage_limit, percentage
        )
    api_usage_status.short_description = 'API Usage'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'timezone', 'language_preference', 'phone_number', 'updated_at')
    list_filter = ('timezone', 'language_preference', 'created_at')
    search_fields = ('user__email', 'user__username', 'phone_number')
    raw_id_fields = ('user',)
