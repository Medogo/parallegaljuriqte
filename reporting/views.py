# reporting/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import CommunityReport, AudioReport, ReportFollowUp
from .serializers import (
    CommunityReportCreateSerializer, CommunityReportSerializer,
    AudioReportCreateSerializer, AudioReportSerializer,
    ReportFollowUpSerializer, UserReportSummarySerializer,
    ReportStatsSerializer, ReportSearchSerializer
)

class CommunityReportCreateView(generics.CreateAPIView):
    """Vue pour créer un signalement communautaire (français)"""
    
    serializer_class = CommunityReportCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Vérifier que l'utilisateur utilise le français
        if request.user.preferred_language != 'FR':
            return Response({
                'error': 'Les signalements écrits ne sont disponibles qu\'en français'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        report = serializer.save()
        
        # Enregistrer l'activité
        from progress.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            activity_type='REPORT_SUBMIT',
            details={
                'report_type': 'text',
                'report_id': str(report.report_id),
                'problem_type': report.problem_type
            }
        )
        
        return Response({
            'message': 'Signalement créé avec succès',
            'report': CommunityReportSerializer(report).data
        }, status=status.HTTP_201_CREATED)

class AudioReportCreateView(generics.CreateAPIView):
    """Vue pour créer un signalement audio (Fon)"""
    
    serializer_class = AudioReportCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Vérifier que l'utilisateur utilise le Fon
        if request.user.preferred_language != 'FON':
            return Response({
                'error': 'Les signalements audio ne sont disponibles qu\'en langue Fon'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        report = serializer.save()
        
        # Enregistrer l'activité
        from progress.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            activity_type='REPORT_SUBMIT',
            details={
                'report_type': 'audio',
                'report_id': str(report.report_id),
                'duration': report.duration
            }
        )
        
        return Response({
            'message': 'Signalement audio créé avec succès',
            'report': AudioReportSerializer(report).data
        }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reports_summary(request):
    """Vue pour récupérer tous les signalements d'un utilisateur"""
    
    user = request.user
    
    # Signalements textuels
    text_reports = CommunityReport.objects.filter(user=user).order_by('-created_at')
    
    # Signalements audio
    audio_reports = AudioReport.objects.filter(user=user).order_by('-created_at')
    
    # Statistiques
    total_reports = text_reports.count() + audio_reports.count()
    pending_count = (
        text_reports.filter(status='PENDING').count() +
        audio_reports.filter(status='PENDING').count()
    )
    resolved_count = (
        text_reports.filter(status='RESOLVED').count() +
        audio_reports.filter(status='RESOLVED').count()
    )
    
    # Dernière date de signalement
    last_report_date = None
    if text_reports.exists() or audio_reports.exists():
        text_last = text_reports.first().created_at if text_reports.exists() else None
        audio_last = audio_reports.first().created_at if audio_reports.exists() else None
        
        if text_last and audio_last:
            last_report_date = max(text_last, audio_last)
        elif text_last:
            last_report_date = text_last
        elif audio_last:
            last_report_date = audio_last
    
    summary_data = {
        'total_reports': total_reports,
        'text_reports': CommunityReportSerializer(text_reports, many=True).data,
        'audio_reports': AudioReportSerializer(audio_reports, many=True).data,
        'pending_count': pending_count,
        'resolved_count': resolved_count,
        'last_report_date': last_report_date
    }
    
    return Response(summary_data)

class CommunityReportDetailView(generics.RetrieveAPIView):
    """Vue pour récupérer les détails d'un signalement textuel"""
    
    serializer_class = CommunityReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # L'utilisateur ne peut voir que ses propres signalements
        return CommunityReport.objects.filter(user=self.request.user)

class AudioReportDetailView(generics.RetrieveAPIView):
    """Vue pour récupérer les détails d'un signalement audio"""
    
    serializer_class = AudioReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # L'utilisateur ne peut voir que ses propres signalements
        return AudioReport.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_follow_ups(request, report_type, report_id):
    """Vue pour récupérer les suivis d'un signalement"""
    
    if report_type == 'text':
        report = get_object_or_404(
            CommunityReport, 
            id=report_id, 
            user=request.user
        )
        follow_ups = ReportFollowUp.objects.filter(
            text_report=report,
            is_public=True
        ).order_by('created_at')
    
    elif report_type == 'audio':
        report = get_object_or_404(
            AudioReport,
            id=report_id,
            user=request.user
        )
        follow_ups = ReportFollowUp.objects.filter(
            audio_report=report,
            is_public=True
        ).order_by('created_at')
    
    else:
        return Response({
            'error': 'Type de signalement invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = ReportFollowUpSerializer(follow_ups, many=True)
    
    return Response({
        'report_type': report_type,
        'report_id': report_id,
        'follow_ups': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporting_statistics(request):
    """Vue pour les statistiques globales de signalement (admin seulement)"""
    
    if not request.user.is_staff:
        return Response({
            'error': 'Accès non autorisé'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Compter les signalements
    total_text_reports = CommunityReport.objects.count()
    total_audio_reports = AudioReport.objects.count()
    total_reports = total_text_reports + total_audio_reports
    
    # Par statut (combiné)
    pending_text = CommunityReport.objects.filter(status='PENDING').count()
    pending_audio = AudioReport.objects.filter(status='PENDING').count()
    pending_reports = pending_text + pending_audio
    
    under_review_text = CommunityReport.objects.filter(status='UNDER_REVIEW').count()
    under_review_audio = AudioReport.objects.filter(status='UNDER_REVIEW').count()
    under_review_reports = under_review_text + under_review_audio
    
    resolved_text = CommunityReport.objects.filter(status='RESOLVED').count()
    resolved_audio = AudioReport.objects.filter(status='RESOLVED').count()
    resolved_reports = resolved_text + resolved_audio
    
    # Par type de problème (pour les signalements textuels)
    justice_reports = CommunityReport.objects.filter(problem_type='JUSTICE').count()
    health_reports = CommunityReport.objects.filter(problem_type='HEALTH').count()
    other_reports = CommunityReport.objects.filter(problem_type='OTHER').count()
    
    # Par période
    week_ago = timezone.now() - timedelta(days=7)
    month_ago = timezone.now() - timedelta(days=30)
    
    reports_this_week = (
        CommunityReport.objects.filter(created_at__gte=week_ago).count() +
        AudioReport.objects.filter(created_at__gte=week_ago).count()
    )
    
    reports_this_month = (
        CommunityReport.objects.filter(created_at__gte=month_ago).count() +
        AudioReport.objects.filter(created_at__gte=month_ago).count()
    )
    
    # Taux de résolution
    resolution_rate = (resolved_reports / total_reports * 100) if total_reports > 0 else 0
    
    # Temps moyen de résolution
    resolved_text_reports = CommunityReport.objects.filter(
        status='RESOLVED',
        resolved_at__isnull=False
    )
    resolved_audio_reports = AudioReport.objects.filter(
        status='RESOLVED',
        # Nous devrons ajouter resolved_at au modèle AudioReport si nécessaire
    )
    
    total_resolution_days = 0
    total_resolved_count = 0
    
    for report in resolved_text_reports:
        days = (report.resolved_at - report.created_at).days
        total_resolution_days += days
        total_resolved_count += 1
    
    average_resolution_time = (
        total_resolution_days / total_resolved_count 
        if total_resolved_count > 0 else 0
    )
    
    stats_data = {
        'total_reports': total_reports,
        'text_reports': total_text_reports,
        'audio_reports': total_audio_reports,
        'pending_reports': pending_reports,
        'under_review_reports': under_review_reports,
        'resolved_reports': resolved_reports,
        'justice_reports': justice_reports,
        'health_reports': health_reports,
        'other_reports': other_reports,
        'reports_this_week': reports_this_week,
        'reports_this_month': reports_this_month,
        'resolution_rate': resolution_rate,
        'average_resolution_time': average_resolution_time
    }
    
    return Response(stats_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_reports(request):
    """Vue pour rechercher dans les signalements (admin seulement)"""
    
    if not request.user.is_staff:
        return Response({
            'error': 'Accès non autorisé'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = ReportSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    search_params = serializer.validated_data
    
    # Recherche dans les signalements textuels
    text_queryset = CommunityReport.objects.all()
    
    if search_params.get('search'):
        search_term = search_params['search']
        text_queryset = text_queryset.filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(location__icontains=search_term)
        )
    
    if search_params.get('problem_type'):
        text_queryset = text_queryset.filter(
            problem_type=search_params['problem_type']
        )
    
    if search_params.get('status'):
        text_queryset = text_queryset.filter(
            status=search_params['status']
        )
    
    if search_params.get('commune'):
        text_queryset = text_queryset.filter(
            commune__icontains=search_params['commune']
        )
    
    if search_params.get('date_from'):
        text_queryset = text_queryset.filter(
            created_at__date__gte=search_params['date_from']
        )
    
    if search_params.get('date_to'):
        text_queryset = text_queryset.filter(
            created_at__date__lte=search_params['date_to']
        )
    
    # Recherche dans les signalements audio
    audio_queryset = AudioReport.objects.all()
    
    if search_params.get('status'):
        audio_queryset = audio_queryset.filter(
            status=search_params['status']
        )
    
    if search_params.get('search'):
        search_term = search_params['search']
        audio_queryset = audio_queryset.filter(
            Q(transcription__icontains=search_term) |
            Q(extracted_location__icontains=search_term)
        )
    
    if search_params.get('date_from'):
        audio_queryset = audio_queryset.filter(
            created_at__date__gte=search_params['date_from']
        )
    
    if search_params.get('date_to'):
        audio_queryset = audio_queryset.filter(
            created_at__date__lte=search_params['date_to']
        )
    
    # Limiter les résultats
    text_results = text_queryset.order_by('-created_at')[:50]
    audio_results = audio_queryset.order_by('-created_at')[:50]
    
    return Response({
        'text_reports': CommunityReportSerializer(text_results, many=True).data,
        'audio_reports': AudioReportSerializer(audio_results, many=True).data,
        'total_found': text_queryset.count() + audio_queryset.count(),
        'search_params': search_params
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporting_module_info(request):
    """Vue pour obtenir les informations du module de signalement"""
    
    user = request.user
    language = user.preferred_language
    
    module_info = {
        'FR': {
            'title': 'Module de signalement communautaire',
            'description': '''
            Ce module vous permet de signaler des situations que vous avez vécues 
            ou observées dans votre communauté.
            
            ## Types de signalements acceptés :
            
            - **Justice :** Problèmes liés à l'accès à la justice, violations des droits
            - **Santé :** Difficultés d'accès aux soins, problèmes de santé publique  
            - **Autre :** Tout autre problème communautaire important
            
            ## Informations requises :
            
            - Description détaillée de la situation
            - Localisation de l'incident
            - Date de l'incident
            - Pièces jointes (optionnel)
            
            ## Confidentialité :
            
            - Vous pouvez choisir de rester anonyme
            - Vos données sont protégées et sécurisées
            - Les signalements sont transmis aux structures partenaires appropriées
            
            **Note :** Ce module ne remplace pas les procédures d'urgence. 
            En cas d'urgence, contactez immédiatement les services compétents.
            ''',
            'form_type': 'text',
            'action_button': 'Créer un signalement'
        },
        'FON': {
            'title': 'Module signalement tɔn',
            'description': '''
            Module sia na mɛ, mi siwu do nuyọnu siwo mi mọ kpo ɖo wò habɔ mɛ.
            
            ## Informations importantes :
            
            - Enregistrement audio maximum 3 minutes
            - Parlez clairement en langue Fon
            - Décrivez la situation et le lieu
            - Votre consentement est requis pour transmettre l'audio
            
            ## Confidentialité :
            
            - Vous pouvez choisir de rester anonyme
            - Votre audio sera écouté par des personnes de confiance
            - Les informations seront transmises aux bonnes structures
            ''',
            'form_type': 'audio',
            'action_button': 'Enregistrer un signalement'
        }
    }
    
    info = module_info.get(language, module_info['FR'])
    
    # Statistiques utilisateur
    user_stats = {
        'total_reports': 0,
        'pending_reports': 0,
        'resolved_reports': 0
    }
    
    if language == 'FR':
        user_reports = CommunityReport.objects.filter(user=user)
        user_stats = {
            'total_reports': user_reports.count(),
            'pending_reports': user_reports.filter(status='PENDING').count(),
            'resolved_reports': user_reports.filter(status='RESOLVED').count()
        }
    else:
        user_reports = AudioReport.objects.filter(user=user)
        user_stats = {
            'total_reports': user_reports.count(),
            'pending_reports': user_reports.filter(status='PENDING').count(),
            'resolved_reports': user_reports.filter(status='RESOLVED').count()
        }
    
    return Response({
        'module_info': info,
        'user_stats': user_stats,
        'user_language': language
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_report(request, report_type, report_id):
    """Vue pour supprimer un signalement (dans les 24h seulement)"""
    
    if report_type == 'text':
        report = get_object_or_404(
            CommunityReport,
            id=report_id,
            user=request.user
        )
    elif report_type == 'audio':
        report = get_object_or_404(
            AudioReport,
            id=report_id,
            user=request.user
        )
    else:
        return Response({
            'error': 'Type de signalement invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Vérifier que le signalement a moins de 24h
    time_diff = timezone.now() - report.created_at
    if time_diff.total_seconds() > 24 * 3600:  # 24 heures
        return Response({
            'error': 'Vous ne pouvez supprimer un signalement que dans les 24h suivant sa création'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Vérifier que le signalement n'est pas encore traité
    if report.status not in ['PENDING']:
        return Response({
            'error': 'Vous ne pouvez pas supprimer un signalement déjà en cours de traitement'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    report.delete()
    
    return Response({
        'message': 'Signalement supprimé avec succès'
    }, status=status.HTTP_204_NO_CONTENT)