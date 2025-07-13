"""
Models for transcript documents.
"""
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os


def transcript_upload_path(instance, filename):
    """Generate upload path for transcript files."""
    return f'transcripts/{instance.user.id}/{filename}'


class TranscriptDocument(models.Model):
    """
    Model for storing transcript documents.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transcripts'
    )
    title = models.CharField(
        max_length=255,
        help_text="Title or description of the transcript"
    )
    original_filename = models.CharField(max_length=255)
    file = models.FileField(
        upload_to=transcript_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['txt'])],
        help_text="Transcript text file"
    )
    content = models.TextField(
        help_text="Text content of the transcript"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes"
    )
    character_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of characters in the content"
    )
    word_count = models.PositiveIntegerField(
        default=0,
        help_text="Estimated number of words in the content"
    )
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether this transcript has been processed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transcript Document'
        verbose_name_plural = 'Transcript Documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.email})"

    def save(self, *args, **kwargs):
        """Override save to calculate word and character counts."""
        if self.content:
            self.character_count = len(self.content)
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)

    @property
    def estimated_tokens(self):
        """Estimate number of tokens (rough approximation)."""
        return max(int(self.character_count / 4), self.word_count)

    def get_file_extension(self):
        """Get file extension."""
        return os.path.splitext(self.original_filename)[1].lower()
