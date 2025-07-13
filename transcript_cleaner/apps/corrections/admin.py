"""
Admin configuration for corrections app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CorrectionJob, CorrectionJobHistory


@admin.register(CorrectionJob)
class CorrectionJobAdmin(admin.ModelAdmin):
    """Correction job admin."""
    
    list_display = ('id', 'user', 'transcript_title', 'processing_mode', 'status', 
                   'model_used', 'cost_display', 'created_at')
    list_filter = ('status', 'processing_mode', 'model_used', 'created_at')
    search_fields = ('user__email', 'transcript__title', 'id')
    readonly_fields = ('created_at', 'updated_at', 'started_at', 'completed_at', 
                      'processing_time', 'total_tokens', 'retry_count')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'transcript', 'wordlist', 'status')
        }),
        ('Configuration', {
            'fields': ('processing_mode', 'custom_prompt', 'model_used')
        }),
        ('Results', {
            'fields': ('corrected_content', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Metrics', {
            'fields': ('cost', 'input_tokens', 'output_tokens', 'total_tokens', 
                      'processing_time', 'retry_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def transcript_title(self, obj):
        """Display transcript title with link."""
        if obj.transcript:
            url = reverse('admin:transcripts_transcriptdocument_change', args=[obj.transcript.pk])
            return format_html('<a href="{}">{}</a>', url, obj.transcript.title)
        return '-'
    transcript_title.short_description = 'Transcript'
    transcript_title.admin_order_field = 'transcript__title'
    
    def cost_display(self, obj):
        """Display cost with color coding."""
        if obj.cost == 0:
            return '-'
        
        if obj.cost > 1:
            color = 'red'
        elif obj.cost > 0.1:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">${:.4f}</span>',
            color, obj.cost
        )
    cost_display.short_description = 'Cost'
    cost_display.admin_order_field = 'cost'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'transcript', 'wordlist')


@admin.register(CorrectionJobHistory)
class CorrectionJobHistoryAdmin(admin.ModelAdmin):
    """Correction job history admin."""
    
    list_display = ('job_id', 'job_user', 'status', 'message_preview', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('job__id', 'job__user__email', 'message')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def job_id(self, obj):
        """Display job ID with link."""
        url = reverse('admin:corrections_correctionjob_change', args=[obj.job.pk])
        return format_html('<a href="{}">{}</a>', url, obj.job.pk)
    job_id.short_description = 'Job ID'
    job_id.admin_order_field = 'job__id'
    
    def job_user(self, obj):
        """Display job user."""
        return obj.job.user.email
    job_user.short_description = 'User'
    job_user.admin_order_field = 'job__user__email'
    
    def message_preview(self, obj):
        """Display message preview."""
        if obj.message:
            preview = obj.message[:100] + ('...' if len(obj.message) > 100 else '')
            return preview
        return '-'
    message_preview.short_description = 'Message'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('job__user')