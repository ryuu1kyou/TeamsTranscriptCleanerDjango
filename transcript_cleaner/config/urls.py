"""
URL configuration for transcript_cleaner project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.conf.urls.i18n import i18n_patterns

# 言語に依存しないURL
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # 言語切り替え用URL
    path('i18n/', include('django.conf.urls.i18n')),
    
    # OAuth callbacks (言語に依存しない)
    path('accounts/', include('allauth.urls')),  # Google OAuth callbacks
    
    # API routes (言語に依存しない)
    path('api/v1/auth/', include('apps.accounts.api_urls')),
    path('api/v1/', include('apps.api.urls')),
    
    # Health check
    path('health/', TemplateView.as_view(template_name='health.html'), name='health'),
]

# 多言語対応URL
urlpatterns += i18n_patterns(
    # Authentication (Google OAuth は上で処理済み)
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('apps.accounts.urls')),
    
    # Main web interface
    path('', lambda request: redirect('transcripts:list') if request.user.is_authenticated else redirect('accounts:login'), name='home'),
    path('transcripts/', include('apps.transcripts.urls')),
    
    prefix_default_language=True,  # 全言語にプレフィックスを付ける
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Debug toolbar in development
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Custom admin site configuration
admin.site.site_header = "Transcript Cleaner Administration"
admin.site.site_title = "Transcript Cleaner Admin"
admin.site.index_title = "Welcome to Transcript Cleaner Administration"
