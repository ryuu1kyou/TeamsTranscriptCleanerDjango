"""
Admin configuration for wordlists app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import WordList, SharedWordList


@admin.register(WordList)
class WordListAdmin(admin.ModelAdmin):
    """Word list admin."""
    
    list_display = ('name', 'user', 'word_count', 'is_shared', 'is_active', 'updated_at')
    list_filter = ('is_shared', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'user__email', 'user__username', 'description')
    readonly_fields = ('created_at', 'updated_at', 'word_count', 'csv_preview', 'validation_errors')
    ordering = ('-updated_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'description')
        }),
        ('CSV Content', {
            'fields': ('csv_file', 'csv_content', 'csv_preview')
        }),
        ('Settings', {
            'fields': ('is_shared', 'is_active')
        }),
        ('Statistics', {
            'fields': ('word_count', 'validation_errors')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def csv_preview(self, obj):
        """Display CSV content preview."""
        if obj.csv_content:
            lines = obj.csv_content.split('\n')[:5]  # Show first 5 lines
            preview = '\n'.join(lines)
            if len(obj.csv_content.split('\n')) > 5:
                preview += '\n... (truncated)'
            return format_html('<pre style="max-width: 400px; overflow: auto;">{}</pre>', preview)
        return '-'
    csv_preview.short_description = 'CSV Preview'
    
    def validation_errors(self, obj):
        """Display CSV validation errors."""
        errors = obj.validate_csv_format()
        if errors:
            error_list = '\n'.join([f"• {error}" for error in errors])
            return format_html('<div style="color: red;"><pre>{}</pre></div>', error_list)
        return format_html('<span style="color: green;">No errors</span>')
    validation_errors.short_description = 'Validation'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(SharedWordList)
class SharedWordListAdmin(admin.ModelAdmin):
    """Shared word list admin."""
    
    list_display = ('wordlist_name', 'wordlist_owner', 'shared_user', 'can_edit', 'shared_at')
    list_filter = ('can_edit', 'shared_at')
    search_fields = ('wordlist__name', 'wordlist__user__email', 'user__email')
    readonly_fields = ('shared_at',)
    ordering = ('-shared_at',)
    
    def wordlist_name(self, obj):
        """Display wordlist name with link."""
        url = reverse('admin:wordlists_wordlist_change', args=[obj.wordlist.pk])
        return format_html('<a href="{}">{}</a>', url, obj.wordlist.name)
    wordlist_name.short_description = 'Word List'
    wordlist_name.admin_order_field = 'wordlist__name'
    
    def wordlist_owner(self, obj):
        """Display wordlist owner."""
        return obj.wordlist.user.email
    wordlist_owner.short_description = 'Owner'
    wordlist_owner.admin_order_field = 'wordlist__user__email'
    
    def shared_user(self, obj):
        """Display shared user."""
        return obj.user.email
    shared_user.short_description = 'Shared With'
    shared_user.admin_order_field = 'user__email'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('wordlist__user', 'user')