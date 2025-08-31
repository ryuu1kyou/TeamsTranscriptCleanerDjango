"""
User models for the transcript cleaner application.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    """
    email = models.EmailField(unique=True)
    organization = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Organization or company name"
    )
    api_usage_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Maximum API usage cost allowed in USD"
    )
    total_api_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=Decimal('0.0000'),
        help_text="Total API cost consumed in USD"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email is verified"
    )
    avatar_url = models.URLField(
        blank=True, 
        null=True,
        help_text="URL for user's profile picture from social login"
    )
    last_login_method = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('google', 'Google'),
        ],
        default='email',
        help_text="Last login method used"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_full_name() or self.username})"

    @property
    def remaining_api_budget(self):
        """Calculate remaining API budget."""
        return self.api_usage_limit - self.total_api_cost

    @property
    def api_budget_percentage_used(self):
        """Calculate percentage of API budget used."""
        if self.api_usage_limit == 0:
            return 100
        return float((self.total_api_cost / self.api_usage_limit) * 100)

    def can_use_api(self, estimated_cost=Decimal('0.01')):
        """Check if user can use API with estimated cost."""
        return (self.total_api_cost + estimated_cost) <= self.api_usage_limit

    def add_api_cost(self, cost):
        """Add API cost to user's total."""
        self.total_api_cost += Decimal(str(cost))
        self.save(update_fields=['total_api_cost'])

    def reset_api_cost(self):
        """Reset user's API cost to zero."""
        self.total_api_cost = Decimal('0.0000')
        self.save(update_fields=['total_api_cost'])
    
    # Role management methods
    def get_roles(self):
        """Get all roles (groups) assigned to this user."""
        return self.groups.all()
    
    def get_role_names(self):
        """Get list of role names assigned to this user."""
        return list(self.groups.values_list('name', flat=True))
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.groups.filter(name=role_name).exists()
    
    def add_role(self, role_name):
        """Add a role to this user."""
        from django.contrib.auth.models import Group
        group, created = Group.objects.get_or_create(name=role_name)
        self.groups.add(group)
    
    def remove_role(self, role_name):
        """Remove a role from this user."""
        from django.contrib.auth.models import Group
        try:
            group = Group.objects.get(name=role_name)
            self.groups.remove(group)
        except Group.DoesNotExist:
            pass
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.is_superuser or self.has_role('admin')
    
    def is_manager(self):
        """Check if user has manager role."""
        return self.is_admin() or self.has_role('manager')
    
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.is_admin() or self.has_role('user_manager')


class UserProfile(models.Model):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, max_length=500)
    phone_number = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=50, default='Asia/Tokyo')
    language_preference = models.CharField(
        max_length=10,
        choices=[
            ('ja', 'Japanese'),
            ('en', 'English'),
        ],
        default='ja'
    )
    notification_preferences = models.JSONField(
        default=dict,
        help_text="User notification preferences"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.email} Profile"
