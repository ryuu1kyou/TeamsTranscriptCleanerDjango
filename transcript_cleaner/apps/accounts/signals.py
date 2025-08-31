"""
Signals for accounts app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login
from allauth.socialaccount.models import SocialLogin
from .models import User, UserProfile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


@receiver(pre_social_login)
def populate_profile_from_social_login(sender, request, sociallogin: SocialLogin, **kwargs):
    """
    ソーシャルログイン時のプロフィール情報自動入力
    既存ユーザーのみ処理する
    """
    # すでに認証済みの場合のみ処理（既存ユーザー）
    if not sociallogin.is_existing:
        return
        
    user = sociallogin.user
    
    try:
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            
            # 基本情報の更新
            if extra_data.get('given_name'):
                user.first_name = extra_data.get('given_name', '')
            if extra_data.get('family_name'):
                user.last_name = extra_data.get('family_name', '')
            
            # プロフィール画像URL
            if extra_data.get('picture'):
                user.avatar_url = extra_data.get('picture', '')
            
            # ログイン方法を記録
            user.last_login_method = 'google'
            
            # メール認証済みとしてマーク
            if user.email and not user.is_verified:
                user.is_verified = True
            
            # セッションから言語設定を取得
            language_preference = request.session.get('language_preference', 'ja')
            
            # ユーザープロフィールの言語設定を更新
            try:
                profile = user.profile
                profile.language_preference = language_preference
                profile.save(update_fields=['language_preference'])
            except UserProfile.DoesNotExist:
                # プロフィールが存在しない場合は作成
                UserProfile.objects.create(
                    user=user,
                    language_preference=language_preference
                )
            
            logger.info(f'Updated user profile from Google login: {user.email}')
            
    except Exception as e:
        logger.error(f'Error updating profile from social login: {str(e)}')
        # エラーが発生してもログイン処理は継続
