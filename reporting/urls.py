# reporting/urls.py
from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    # Informations du module
    path('info/', views.reporting_module_info, name='reporting_module_info'),
    
    # Création de signalements
    path('text/create/', views.CommunityReportCreateView.as_view(), name='create_text_report'),
    path('audio/create/', views.AudioReportCreateView.as_view(), name='create_audio_report'),
    
    # Consultation des signalements
    path('summary/', views.user_reports_summary, name='user_reports_summary'),
    path('text/<int:pk>/', views.CommunityReportDetailView.as_view(), name='text_report_detail'),
    path('audio/<int:pk>/', views.AudioReportDetailView.as_view(), name='audio_report_detail'),
    
    # Suivi des signalements
    path('follow-ups/<str:report_type>/<int:report_id>/', views.report_follow_ups, name='report_follow_ups'),
    
    # Suppression (dans les 24h)
    path('delete/<str:report_type>/<int:report_id>/', views.delete_report, name='delete_report'),
    
    # Administration (staff seulement)
    path('statistics/', views.reporting_statistics, name='reporting_statistics'),
    path('search/', views.search_reports, name='search_reports'),
]