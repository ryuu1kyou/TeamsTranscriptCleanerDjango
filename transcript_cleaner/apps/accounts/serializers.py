"""
Serializers for accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'organization', 'full_name', 'api_usage_limit',
            'total_api_cost', 'remaining_api_budget', 'api_budget_percentage_used',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'full_name', 'remaining_api_budget', 
                           'api_budget_percentage_used', 'date_joined', 'last_login']


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates."""
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'organization'
        ]
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        user = self.instance
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("このユーザー名は既に使用されています。")
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        user = self.instance
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("このメールアドレスは既に使用されています。")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("新しいパスワードが一致しません。")
        return attrs


class APIUsageSerializer(serializers.Serializer):
    """Serializer for API usage data."""
    
    total_api_cost = serializers.DecimalField(max_digits=10, decimal_places=4)
    api_usage_limit = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining_api_budget = serializers.DecimalField(max_digits=10, decimal_places=2)
    api_budget_percentage_used = serializers.FloatField()
    monthly_cost = serializers.DecimalField(max_digits=10, decimal_places=4)
    total_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    pending_jobs = serializers.IntegerField()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'organization', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("パスワードが一致しません。")
        return attrs
    
    def create(self, validated_data):
        """Create new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user
