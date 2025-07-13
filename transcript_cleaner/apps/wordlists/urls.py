"""
URL configuration for wordlists app.
"""
from django.urls import path
from . import views

app_name = 'wordlists'

urlpatterns = [
    path('', views.wordlist_list, name='list'),
    path('create/', views.wordlist_create, name='create'),
    path('<int:pk>/', views.wordlist_detail, name='detail'),
    path('<int:pk>/edit/', views.wordlist_edit, name='edit'),
    path('<int:pk>/delete/', views.wordlist_delete, name='delete'),
    path('<int:pk>/download/', views.wordlist_download, name='download'),
    path('api/', views.WordListAPIView.as_view(), name='api'),
]