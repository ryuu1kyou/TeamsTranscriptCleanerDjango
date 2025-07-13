"""
Models for word correction lists.
"""
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import csv
import io


def wordlist_upload_path(instance, filename):
    """Generate upload path for wordlist files."""
    return f'wordlists/{instance.user.id}/{filename}'


class WordList(models.Model):
    """
    Model for storing word correction lists.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wordlists'
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the word list"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the word list"
    )
    csv_file = models.FileField(
        upload_to=wordlist_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        blank=True,
        null=True,
        help_text="CSV file containing word corrections"
    )
    csv_content = models.TextField(
        help_text="CSV content as text"
    )
    word_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of word pairs in the list"
    )
    is_shared = models.BooleanField(
        default=False,
        help_text="Whether this word list is shared with other users"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this word list is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Word List'
        verbose_name_plural = 'Word Lists'
        ordering = ['-updated_at']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def save(self, *args, **kwargs):
        """Override save to calculate word count."""
        if self.csv_content:
            self.word_count = self.get_word_count()
        super().save(*args, **kwargs)

    def get_word_count(self):
        """Count the number of word pairs in the CSV content."""
        try:
            csv_reader = csv.reader(io.StringIO(self.csv_content))
            # Skip header row
            next(csv_reader, None)
            count = sum(1 for row in csv_reader if len(row) >= 2)
            return count
        except Exception:
            return 0

    def get_word_pairs(self):
        """Parse CSV content and return list of word pairs."""
        word_pairs = []
        try:
            csv_reader = csv.reader(io.StringIO(self.csv_content))
            # Skip header row
            next(csv_reader, None)
            for row in csv_reader:
                if len(row) >= 2:
                    word_pairs.append({
                        'incorrect': row[0].strip(),
                        'correct': row[1].strip()
                    })
        except Exception:
            pass
        return word_pairs

    def validate_csv_format(self):
        """Validate CSV format and return any errors."""
        errors = []
        try:
            csv_reader = csv.reader(io.StringIO(self.csv_content))
            header = next(csv_reader, None)
            
            if not header or len(header) < 2:
                errors.append("CSV must have at least 2 columns")
            
            row_count = 0
            for row_num, row in enumerate(csv_reader, start=2):
                if len(row) < 2:
                    errors.append(f"Row {row_num}: Must have at least 2 columns")
                elif not row[0].strip() or not row[1].strip():
                    errors.append(f"Row {row_num}: Both columns must have values")
                row_count += 1
            
            if row_count == 0:
                errors.append("CSV must contain at least one data row")
                
        except Exception as e:
            errors.append(f"CSV parsing error: {str(e)}")
        
        return errors


class SharedWordList(models.Model):
    """
    Model for tracking shared word lists access.
    """
    wordlist = models.ForeignKey(
        WordList,
        on_delete=models.CASCADE,
        related_name='shared_access'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_wordlists'
    )
    can_edit = models.BooleanField(
        default=False,
        help_text="Whether the user can edit this shared word list"
    )
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Shared Word List'
        verbose_name_plural = 'Shared Word Lists'
        unique_together = ['wordlist', 'user']

    def __str__(self):
        return f"{self.wordlist.name} shared with {self.user.email}"
