"""
URL configuration for corrections app.
"""
from django.urls import path
from . import views

app_name = 'corrections'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/retry/', views.job_retry, name='job_retry'),
    path('<int:pk>/cancel/', views.job_cancel, name='job_cancel'),
    path('<int:pk>/download/', views.job_download, name='job_download'),
    path('<int:pk>/copy-to-new/', views.job_copy_to_new, name='job_copy_to_new'),
    path('api/', views.CorrectionAPIView.as_view(), name='api'),
]