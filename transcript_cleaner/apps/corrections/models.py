"""
Models for correction jobs and results.
"""
from django.db import models
from django.conf import settings
from decimal import Decimal


class CorrectionJob(models.Model):
    """
    Model for correction processing jobs.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PROCESSING_MODE_CHOICES = [
        ('proofreading', 'Proofreading (Typo Correction)'),
        ('grammar', 'Grammar Correction'),
        ('summary', 'Summary Generation'),
        ('custom', 'Custom Processing'),
    ]
    
    MODEL_CHOICES = [
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4-turbo', 'GPT-4 Turbo'),
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='correction_jobs'
    )
    transcript = models.ForeignKey(
        'transcripts.TranscriptDocument',
        on_delete=models.CASCADE,
        related_name='correction_jobs'
    )
    wordlist = models.ForeignKey(
        'wordlists.WordList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='correction_jobs'
    )
    
    # Job configuration
    processing_mode = models.CharField(
        max_length=20,
        choices=PROCESSING_MODE_CHOICES,
        default='proofreading'
    )
    custom_prompt = models.TextField(
        blank=True,
        help_text="Custom instructions for processing"
    )
    model_used = models.CharField(
        max_length=50,
        choices=MODEL_CHOICES,
        default='gpt-4o'
    )
    
    # Job status and results
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    corrected_content = models.TextField(
        blank=True,
        help_text="Corrected text output"
    )
    
    # Processing metadata
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="API cost for this job in USD"
    )
    input_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Number of input tokens used"
    )
    output_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Number of output tokens generated"
    )
    processing_time = models.DurationField(
        null=True,
        blank=True,
        help_text="Time taken to process"
    )
    
    # Error handling
    error_message = models.TextField(
        blank=True,
        help_text="Error message if processing failed"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Correction Job'
        verbose_name_plural = 'Correction Jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id}: {self.get_processing_mode_display()} - {self.status}"

    @property
    def is_completed(self):
        """Check if job is completed (successfully or with error)."""
        return self.status in ['completed', 'failed', 'cancelled']

    @property
    def is_successful(self):
        """Check if job completed successfully."""
        return self.status == 'completed'

    @property
    def total_tokens(self):
        """Get total tokens used."""
        return self.input_tokens + self.output_tokens

    def mark_as_processing(self):
        """Mark job as processing."""
        from django.utils import timezone
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def mark_as_completed(self, corrected_content, cost=0, input_tokens=0, output_tokens=0):
        """Mark job as completed successfully."""
        from django.utils import timezone
        self.status = 'completed'
        self.corrected_content = corrected_content
        self.cost = Decimal(str(cost))
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.completed_at = timezone.now()
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
            
        self.save(update_fields=[
            'status', 'corrected_content', 'cost', 'input_tokens', 
            'output_tokens', 'completed_at', 'processing_time'
        ])
        
        # Add cost to user's total
        self.user.add_api_cost(cost)

    def mark_as_failed(self, error_message):
        """Mark job as failed."""
        from django.utils import timezone
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
            
        self.save(update_fields=['status', 'error_message', 'completed_at', 'processing_time'])


class CorrectionJobHistory(models.Model):
    """
    Model for tracking correction job history and changes.
    """
    job = models.ForeignKey(
        CorrectionJob,
        on_delete=models.CASCADE,
        related_name='history'
    )
    status = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Correction Job History'
        verbose_name_plural = 'Correction Job Histories'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Job {self.job.id} - {self.status} at {self.timestamp}"
