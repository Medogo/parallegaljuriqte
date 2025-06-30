# modules/urls.py
from django.urls import path
from . import views

app_name = 'modules'

urlpatterns = [
    # Liste et détails des modules
    path('', views.ModuleListView.as_view(), name='module_list'),
    path('<int:pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('search/', views.ModuleSearchView.as_view(), name='module_search'),
    
    # Contenu d'introduction
    path('intro/', views.intro_content, name='intro_content'),
    
    # Statut des modules pour l'utilisateur
    path('status/', views.user_module_status, name='user_module_status'),
    
    # Gestion des quiz
    path('quiz/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/attempts/', views.user_quiz_attempts, name='user_quiz_attempts'),
    path('quiz/attempts/<int:module_id>/', views.user_quiz_attempts, name='user_quiz_attempts_module'),
    path('quiz/best/<int:module_id>/', views.quiz_best_attempt, name='quiz_best_attempt'),
    
    # Suivi audio
    path('audio/progress/', views.track_audio_progress, name='track_audio_progress'),
    
    # Statistiques (admin)
    path('stats/<int:module_id>/', views.module_stats, name='module_stats'),
]