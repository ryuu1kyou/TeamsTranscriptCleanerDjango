from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from .models import User


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    カスタムアカウントアダプター
    """
    pass


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    カスタムソーシャルアカウントアダプター
    Google認証成功で自動ユーザー作成
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        ソーシャルログイン前の処理
        メールアドレスで既存ユーザーと自動連携
        """
        # すでに認証済みの場合はスキップ
        if sociallogin.is_existing:
            return
            
        # メールアドレスを取得
        email = None
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email')
        
        if not email:
            messages.error(request, 'ソーシャルアカウントからメールアドレスを取得できませんでした。')
            raise ImmediateHttpResponse(redirect('accounts:login'))
        
        # 既存ユーザーをチェック（メールアドレスベース）
        try:
            existing_user = User.objects.get(email=email)
            # 既存ユーザーが見つかった場合、ソーシャルアカウントを関連付け
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # 既存ユーザーが見つからない場合は新規作成を許可
            # django-allauthのデフォルト処理で自動作成される
            pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        新規ユーザー保存処理
        Google情報から基本的なユーザー情報を設定
        """
        user = super().save_user(request, sociallogin, form)
        
        # Google情報から追加のユーザー情報を設定
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            
            user.first_name = extra_data.get('given_name', '')
            user.last_name = extra_data.get('family_name', '')
            user.avatar_url = extra_data.get('picture', '')
            user.is_verified = True  # Google認証済みとしてマーク
            user.last_login_method = 'google'
            user.save()
        
        return user