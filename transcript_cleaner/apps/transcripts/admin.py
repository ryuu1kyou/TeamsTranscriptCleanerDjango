"""
Admin configuration for transcripts app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import TranscriptDocument


@admin.register(TranscriptDocument)
class TranscriptDocumentAdmin(admin.ModelAdmin):
    """Transcript document admin."""
    
    list_display = ('title', 'user', 'file_size_display', 'character_count', 
                   'word_count', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'created_at', 'updated_at')
    search_fields = ('title', 'user__email', 'user__username', 'original_filename')
    readonly_fields = ('created_at', 'updated_at', 'file_size', 'character_count', 
                      'word_count', 'estimated_tokens', 'content_preview')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'original_filename', 'file')
        }),
        ('Content', {
            'fields': ('content_preview', 'content'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('file_size', 'character_count', 'word_count', 'estimated_tokens', 'is_processed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        """Display file size in human readable format."""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'File Size'
    file_size_display.admin_order_field = 'file_size'
    
    def content_preview(self, obj):
        """Display content preview."""
        if obj.content:
            preview = obj.content[:200] + ('...' if len(obj.content) > 200 else '')
            return format_html('<div style="max-width: 300px; word-wrap: break-word;">{}</div>', preview)
        return '-'
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')