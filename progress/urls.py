# progress/urls.py
from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    # Progression globale
    path('', views.UserProgressView.as_view(), name='user_progress'),
    path('summary/', views.progress_summary, name='progress_summary'),
    
    # Progression des modules
    path('modules/', views.ModuleProgressListView.as_view(), name='module_progress_list'),
    path('modules/<int:module_id>/', views.ModuleProgressDetailView.as_view(), name='module_progress_detail'),
    path('modules/<int:module_id>/start/', views.mark_module_started, name='mark_module_started'),
    
    # Certificats
    path('certificate/request/', views.request_certificate, name='request_certificate'),
    path('certificate/verify/<str:verification_code>/', views.verify_certificate, name='verify_certificate'),
    path('certificate/fon-info/', views.fon_certificate_info, name='fon_certificate_info'),
    
    # Activités
    path('activities/', views.UserActivityListView.as_view(), name='user_activities'),
    
    # Classement et statistiques
    path('leaderboard/', views.user_leaderboard, name='user_leaderboard'),
    path('statistics/', views.progress_statistics, name='progress_statistics'),
]