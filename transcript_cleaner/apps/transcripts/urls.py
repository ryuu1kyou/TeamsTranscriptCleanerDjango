"""
URL configuration for transcripts app.
"""
from django.urls import path
from . import views

app_name = 'transcripts'

urlpatterns = [
    path('', views.main_workspace, name='list'),
    path('api/', views.TranscriptAPIView.as_view(), name='api'),
]