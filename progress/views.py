# progress/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth import get_user_model

from .models import ModuleProgress, Certificate, OverallProgress, UserActivity
from .serializers import (
    ModuleProgressSerializer, CertificateSerializer, OverallProgressSerializer,
    UserActivitySerializer, ActivityCreateSerializer, ProgressSummarySerializer,
    CertificateRequestSerializer, CertificateVerificationSerializer,
    FonUserProgressSerializer, ProgressStatsSerializer
)
from modules.models import Module

User = get_user_model()

class UserProgressView(generics.RetrieveAPIView):
    """Vue pour récupérer la progression globale de l'utilisateur"""
    
    serializer_class = OverallProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        progress, created = OverallProgress.objects.get_or_create(
            user=self.request.user
        )
        
        # Mettre à jour la progression
        progress.update_progress()
        
        return progress

class ModuleProgressListView(generics.ListAPIView):
    """Vue pour lister la progression des modules de l'utilisateur"""
    
    serializer_class = ModuleProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ModuleProgress.objects.filter(
            user=self.request.user
        ).select_related('module').order_by('module__number')

class ModuleProgressDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour récupérer/mettre à jour la progression d'un module spécifique"""
    
    serializer_class = ModuleProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id, is_active=True)
        
        progress, created = ModuleProgress.objects.get_or_create(
            user=self.request.user,
            module=module
        )
        
        return progress

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progress_summary(request):
    """Vue pour récupérer un résumé complet de la progression"""
    
    user = request.user
    
    # Progression globale
    overall_progress, created = OverallProgress.objects.get_or_create(user=user)
    overall_progress.update_progress()
    
    # Progression des modules
    module_progress = ModuleProgress.objects.filter(
        user=user
    ).select_related('module').order_by('module__number')
    
    # Activités récentes (dernières 10)
    recent_activities = UserActivity.objects.filter(
        user=user
    ).select_related('module')[:10]
    
    # Certificats
    certificates = Certificate.objects.filter(user=user, is_valid=True)
    
    # Statistiques additionnelles
    total_time_spent = module_progress.aggregate(
        total=Sum('total_listening_time')
    )['total'] or 0
    
    days_since_start = (timezone.now().date() - user.date_joined.date()).days
    
    last_activity = recent_activities.first()
    last_activity_date = last_activity.timestamp if last_activity else user.date_joined
    
    # Modules terminés cette semaine
    week_ago = timezone.now() - timedelta(days=7)
    modules_this_week = module_progress.filter(
        completed_at__gte=week_ago
    ).count()
    
    summary_data = {
        'overall_progress': OverallProgressSerializer(overall_progress).data,
        'module_progress': ModuleProgressSerializer(module_progress, many=True).data,
        'recent_activities': UserActivitySerializer(recent_activities, many=True).data,
        'certificates': CertificateSerializer(certificates, many=True).data,
        'total_time_spent': total_time_spent,
        'days_since_start': days_since_start,
        'last_activity_date': last_activity_date,
        'modules_this_week': modules_this_week
    }
    
    return Response(summary_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_certificate(request):
    """Vue pour demander un certificat"""
    
    user = request.user
    
    # Vérifier si l'utilisateur utilise le français
    if user.preferred_language != 'FR':
        # Retourner les instructions pour les utilisateurs Fon
        serializer = FonUserProgressSerializer()
        data = serializer.to_representation(user)
        return Response(data)
    
    # Vérifier s'il existe déjà un certificat
    existing_certificate = Certificate.objects.filter(
        user=user,
        is_valid=True
    ).first()
    
    if existing_certificate:
        return Response({
            'message': 'Vous avez déjà un certificat valide',
            'certificate': CertificateSerializer(existing_certificate).data
        })
    
    # Valider la demande
    serializer = CertificateRequestSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Créer le certificat
    from modules.models import UserQuizAttempt
    
    # Calculer le score moyen
    training_modules = Module.objects.filter(is_active=True, number__lt=10)
    best_scores = []
    
    for module in training_modules:
        best_attempt = UserQuizAttempt.objects.filter(
            user=user,
            module=module,
            is_passed=True
        ).order_by('-score').first()
        
        if best_attempt:
            best_scores.append(best_attempt.score)
    
    average_score = sum(best_scores) / len(best_scores) if best_scores else 0
    
    # Créer le certificat
    certificate = Certificate.objects.create(
        user=user,
        full_name=serializer.validated_data['full_name'],
        total_modules_completed=len(best_scores),
        average_score=average_score
    )
    
    # Marquer la progression comme demandée
    overall_progress = OverallProgress.objects.get(user=user)
    overall_progress.certificate_requested = True
    overall_progress.save()
    
    # Enregistrer l'activité
    UserActivity.objects.create(
        user=user,
        activity_type='CERTIFICATE_REQUEST',
        details={'certificate_id': str(certificate.certificate_id)}
    )
    
    return Response({
        'message': 'Certificat généré avec succès',
        'certificate': CertificateSerializer(certificate).data
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_certificate(request, verification_code):
    """Vue pour vérifier un certificat"""
    
    try:
        certificate = Certificate.objects.get(
            verification_code=verification_code,
            is_valid=True
        )
        
        verification_data = {
            'is_valid': True,
            'certificate': {
                'full_name': certificate.full_name,
                'completion_date': certificate.completion_date,
                'total_modules_completed': certificate.total_modules_completed,
                'average_score': certificate.average_score,
                'verification_code': certificate.verification_code,
                'signed_by': certificate.signed_by,
                'signature_date': certificate.signature_date
            },
            'verified_at': timezone.now()
        }
        
        return Response(verification_data)
        
    except Certificate.DoesNotExist:
        return Response({
            'is_valid': False,
            'message': 'Certificat non trouvé ou invalide'
        }, status=status.HTTP_404_NOT_FOUND)

class UserActivityListView(generics.ListCreateAPIView):
    """Vue pour lister et créer des activités utilisateur"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ActivityCreateSerializer
        return UserActivitySerializer
    
    def get_queryset(self):
        return UserActivity.objects.filter(
            user=self.request.user
        ).select_related('module').order_by('-timestamp')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_leaderboard(request):
    """Vue pour afficher le classement anonymisé"""
    
    # Récupérer tous les utilisateurs avec leur progression
    users_progress = OverallProgress.objects.select_related('user').all()
    
    # Créer le classement
    leaderboard = []
    for progress in users_progress.order_by('-completion_percentage', '-completed_modules'):
        leaderboard.append({
            'completion_percentage': progress.completion_percentage,
            'average_score': progress.average_quiz_score,
            'completed_modules': progress.completed_modules,
            'commune': progress.user.commune,
            'is_current_user': progress.user == request.user
        })
    
    # Ajouter les rangs
    for i, entry in enumerate(leaderboard, 1):
        entry['rank'] = i
    
    # Limiter aux 50 premiers et inclure l'utilisateur actuel s'il n'y est pas
    top_50 = leaderboard[:50]
    current_user_in_top = any(entry['is_current_user'] for entry in top_50)
    
    if not current_user_in_top:
        current_user_entry = next(
            (entry for entry in leaderboard if entry['is_current_user']),
            None
        )
        if current_user_entry:
            top_50.append(current_user_entry)
    
    return Response({
        'leaderboard': top_50,
        'total_users': len(leaderboard),
        'user_rank': next(
            (entry['rank'] for entry in leaderboard if entry['is_current_user']),
            None
        )
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progress_statistics(request):
    """Vue pour les statistiques globales (admin seulement)"""
    
    if not request.user.is_staff:
        return Response(
            {'error': 'Accès non autorisé'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Statistiques générales
    total_users = User.objects.count()
    
    # Utilisateurs actifs cette semaine
    week_ago = timezone.now() - timedelta(days=7)
    active_users_week = UserActivity.objects.filter(
        timestamp__gte=week_ago
    ).values('user').distinct().count()
    
    # Taux de completion
    completed_users = OverallProgress.objects.filter(
        completion_percentage=100
    ).count()
    completion_rate = (completed_users / total_users) * 100 if total_users > 0 else 0
    
    # Temps moyen de completion
    completed_progress = OverallProgress.objects.filter(
        completed_at__isnull=False
    )
    
    if completed_progress.exists():
        completion_times = [
            (p.completed_at - p.started_at).days
            for p in completed_progress
        ]
        average_completion_time = sum(completion_times) / len(completion_times)
    else:
        average_completion_time = 0
    
    # Top communes
    top_communes = User.objects.values('commune').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Taux de completion par module
    modules = Module.objects.filter(is_active=True, number__lt=10)
    module_completion_rates = {}
    
    for module in modules:
        if request.user.objects.filter(preferred_language='FR').exists():
            # Statistiques quiz
            from modules.models import UserQuizAttempt
            passed_users = UserQuizAttempt.objects.filter(
                module=module,
                is_passed=True
            ).values('user').distinct().count()
        else:
            # Statistiques audio
            passed_users = ModuleProgress.objects.filter(
                module=module,
                is_completed=True
            ).count()
        
        rate = (passed_users / total_users) * 100 if total_users > 0 else 0
        module_completion_rates[f"Module {module.number}"] = rate
    
    # Répartition par langue
    french_users = User.objects.filter(preferred_language='FR').count()
    fon_users = User.objects.filter(preferred_language='FON').count()
    
    # Certificats
    total_certificates = Certificate.objects.filter(is_valid=True).count()
    
    month_ago = timezone.now() - timedelta(days=30)
    certificates_this_month = Certificate.objects.filter(
        completion_date__gte=month_ago,
        is_valid=True
    ).count()
    
    stats_data = {
        'total_users': total_users,
        'active_users_week': active_users_week,
        'completion_rate': completion_rate,
        'average_completion_time': average_completion_time,
        'top_communes': list(top_communes),
        'module_completion_rates': module_completion_rates,
        'french_users': french_users,
        'fon_users': fon_users,
        'total_certificates': total_certificates,
        'certificates_this_month': certificates_this_month
    }
    
    return Response(stats_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_module_started(request, module_id):
    """Vue pour marquer qu'un module a été commencé"""
    
    module = get_object_or_404(Module, id=module_id, is_active=True)
    user = request.user
    
    # Créer ou récupérer la progression
    progress, created = ModuleProgress.objects.get_or_create(
        user=user,
        module=module
    )
    
    # Enregistrer l'activité
    UserActivity.objects.create(
        user=user,
        activity_type='MODULE_VIEW',
        module=module,
        details={'action': 'started'}
    )
    
    return Response({
        'message': f'Module {module.number} marqué comme commencé',
        'progress': ModuleProgressSerializer(progress).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fon_certificate_info(request):
    """Vue spéciale pour les informations de certificat pour les utilisateurs Fon"""
    
    user = request.user
    
    if user.preferred_language != 'FON':
        return Response({
            'error': 'Cette vue est réservée aux utilisateurs en langue Fon'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = FonUserProgressSerializer()
    data = serializer.to_representation(user)
    
    return Response(data)