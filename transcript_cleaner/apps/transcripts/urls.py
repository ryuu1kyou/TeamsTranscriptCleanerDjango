"""
URL configuration for transcripts app.
"""
from django.urls import path
from . import views

app_name = 'transcripts'

urlpatterns = [
    path('', views.transcript_list, name='list'),
    path('workspace/', views.main_workspace, name='workspace'),
    path('upload/', views.transcript_upload, name='upload'),
    path('process/', views.transcript_process, name='process'),
    path('<int:pk>/', views.transcript_detail, name='detail'),
    path('<int:pk>/delete/', views.transcript_delete, name='delete'),
    path('api/', views.TranscriptAPIView.as_view(), name='api'),
]