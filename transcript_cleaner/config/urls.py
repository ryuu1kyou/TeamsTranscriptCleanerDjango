"""
URL configuration for transcript_cleaner project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    # django-allauth URLs should come before the default auth URLs
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('apps.accounts.urls')),
    
    # Main web interface
    path('', lambda request: redirect('transcripts:workspace') if request.user.is_authenticated else TemplateView.as_view(template_name='index.html')(request), name='home'),
    path('transcripts/', include('apps.transcripts.urls')),
    path('corrections/', include('apps.corrections.urls')),
    path('wordlists/', include('apps.wordlists.urls')),
    
    # API routes
    path('api/v1/auth/', include('apps.accounts.api_urls')),
    path('api/v1/', include('apps.api.urls')),
    
    # Health check
    path('health/', TemplateView.as_view(template_name='health.html'), name='health'),
]

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
