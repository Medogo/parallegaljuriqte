# modules/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Module, QuizQuestion, AnswerChoice, 
    UserQuizAttempt, UserQuizAnswer
)
from .serializers import (
    ModuleListSerializer, ModuleDetailSerializer,
    QuizSubmissionSerializer, UserQuizAttemptSerializer,
    QuizResultSerializer, AudioProgressSerializer,
    ModuleStatsSerializer
)

class ModuleListView(generics.ListAPIView):
    """Vue pour lister tous les modules"""
    
    serializer_class = ModuleListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Module.objects.filter(is_active=True).order_by('number')

class ModuleDetailView(generics.RetrieveAPIView):
    """Vue pour les détails d'un module"""
    
    serializer_class = ModuleDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Module.objects.filter(is_active=True)
    
    def get_object(self):
        module_id = self.kwargs.get('pk')
        module = get_object_or_404(Module, id=module_id, is_active=True)
        return module

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request):
    """Vue pour soumettre un quiz"""
    
    serializer = QuizSubmissionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    module = Module.objects.get(id=data['module_id'])
    user = request.user
    
    # Vérifier que l'utilisateur préfère le français
    if user.preferred_language != 'FR':
        return Response(
            {'error': 'Les quiz ne sont disponibles qu\'en français'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculer le numéro de tentative
    last_attempt = UserQuizAttempt.objects.filter(
        user=user, module=module
    ).order_by('-attempt_number').first()
    
    attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
    
    # Récupérer toutes les questions du module
    questions = module.get_quiz_questions()
    
    if not questions.exists():
        return Response(
            {'error': 'Aucune question trouvée pour ce module'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Créer la tentative
    quiz_attempt = UserQuizAttempt.objects.create(
        user=user,
        module=module,
        attempt_number=attempt_number,
        started_at=data['started_at'],
        total_questions=questions.count(),
        score=0,  # Sera calculé
        correct_answers=0  # Sera calculé
    )
    
    # Traiter les réponses
    correct_answers = 0
    total_points_possible = 0
    total_points_earned = 0
    user_answers_data = {}
    
    for answer_data in data['answers']:
        question = answer_data['question']
        selected_choices = answer_data['selected_choices']
        
        # Créer la réponse utilisateur
        user_answer = UserQuizAnswer.objects.create(
            attempt=quiz_attempt,
            question=question
        )
        user_answer.selected_choices.set(selected_choices)
        
        # Calculer si la réponse est correcte
        correct_choice_ids = set(
            question.get_correct_answers().values_list('id', flat=True)
        )
        selected_choice_ids = set(choice.id for choice in selected_choices)
        
        is_correct = correct_choice_ids == selected_choice_ids
        points_earned = question.points if is_correct else 0
        
        user_answer.is_correct = is_correct
        user_answer.points_earned = points_earned
        user_answer.save()
        
        if is_correct:
            correct_answers += 1
        
        total_points_possible += question.points
        total_points_earned += points_earned
        
        # Stocker les réponses pour le résultat
        user_answers_data[question.id] = {
            'selected_choices': [choice.id for choice in selected_choices],
            'is_correct': is_correct,
            'points_earned': points_earned
        }
    
    # Calculer le score final
    score_percentage = (total_points_earned / total_points_possible) * 100 if total_points_possible > 0 else 0
    
    # Mettre à jour la tentative
    quiz_attempt.correct_answers = correct_answers
    quiz_attempt.score = score_percentage
    quiz_attempt.save()  # is_passed sera calculé automatiquement
    
    # Préparer la réponse
    questions_with_answers = []
    for question in questions:
        question_data = {
            'id': question.id,
            'order': question.order,
            'question_type': question.question_type,
            'question_text': question.question_text,
            'explanation': question.explanation,
            'points': question.points,
            'answer_choices': [
                {
                    'id': choice.id,
                    'choice_text': choice.choice_text,
                    'is_correct': choice.is_correct,
                    'order': choice.order
                }
                for choice in question.answer_choices.all().order_by('order')
            ]
        }
        questions_with_answers.append(question_data)
    
    # Message de résultat
    passed = quiz_attempt.is_passed
    if passed:
        message = f"Félicitations ! Vous avez réussi le quiz avec {score_percentage:.1f}%"
    else:
        message = f"Score: {score_percentage:.1f}%. Il faut 80% pour valider le module. Vous pouvez recommencer."
    
    result_data = {
        'attempt': {
            'id': quiz_attempt.id,
            'module_number': module.number,
            'module_title': module.title,
            'attempt_number': quiz_attempt.attempt_number,
            'score': quiz_attempt.score,
            'total_questions': quiz_attempt.total_questions,
            'correct_answers': quiz_attempt.correct_answers,
            'is_passed': quiz_attempt.is_passed,
            'started_at': quiz_attempt.started_at,
            'completed_at': quiz_attempt.completed_at
        },
        'questions_with_answers': questions_with_answers,
        'user_answers': user_answers_data,
        'passed': passed,
        'message': message
    }
    
    return Response(result_data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_quiz_attempts(request, module_id=None):
    """Vue pour récupérer les tentatives de quiz d'un utilisateur"""
    
    queryset = UserQuizAttempt.objects.filter(user=request.user)
    
    if module_id:
        module = get_object_or_404(Module, id=module_id, is_active=True)
        queryset = queryset.filter(module=module)
    
    attempts = queryset.order_by('-completed_at')
    serializer = UserQuizAttemptSerializer(attempts, many=True)
    
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_best_attempt(request, module_id):
    """Vue pour récupérer la meilleure tentative d'un utilisateur pour un module"""
    
    module = get_object_or_404(Module, id=module_id, is_active=True)
    
    best_attempt = UserQuizAttempt.objects.filter(
        user=request.user,
        module=module
    ).order_by('-score', '-completed_at').first()
    
    if not best_attempt:
        return Response(
            {'message': 'Aucune tentative trouvée pour ce module'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = UserQuizAttemptSerializer(best_attempt)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_audio_progress(request):
    """Vue pour suivre la progression audio"""
    
    serializer = AudioProgressSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    module = Module.objects.get(id=data['module_id'])
    user = request.user
    
    # Vérifier que l'utilisateur préfère le Fon
    if user.preferred_language != 'FON':
        return Response(
            {'error': 'Le suivi audio n\'est disponible qu\'en langue Fon'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Importer le modèle de progression (sera créé dans progress/models.py)
    from progress.models import ModuleProgress
    
    # Récupérer ou créer la progression
    progress, created = ModuleProgress.objects.get_or_create(
        user=user,
        module=module,
        defaults={
            'progress_percentage': data['progress_percentage'],
            'last_audio_position': data['current_time']
        }
    )
    
    if not created:
        # Mettre à jour seulement si la progression a avancé
        if data['progress_percentage'] > progress.progress_percentage:
            progress.progress_percentage = data['progress_percentage']
            progress.last_audio_position = data['current_time']
            progress.updated_at = timezone.now()
            progress.save()
    
    # Marquer comme complété si 100%
    if data['progress_percentage'] >= 100:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()
    
    return Response({
        'message': 'Progression mise à jour',
        'progress_percentage': progress.progress_percentage,
        'is_completed': progress.is_completed
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def module_stats(request, module_id):
    """Vue pour les statistiques d'un module (admin)"""
    
    # Vérifier les permissions admin
    if not request.user.is_staff:
        return Response(
            {'error': 'Accès non autorisé'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    module = get_object_or_404(Module, id=module_id, is_active=True)
    
    # Statistiques des quiz (pour les modules français)
    if not module.is_reporting_module:
        quiz_stats = UserQuizAttempt.objects.filter(module=module).aggregate(
            total_attempts=Count('id'),
            unique_users=Count('user', distinct=True),
            average_score=Avg('score'),
            passed_attempts=Count('id', filter=Q(is_passed=True))
        )
        
        completion_rate = 0
        if quiz_stats['total_attempts'] > 0:
            completion_rate = (quiz_stats['passed_attempts'] / quiz_stats['total_attempts']) * 100
    
    # Statistiques audio (pour tous les modules)
    from progress.models import ModuleProgress
    audio_stats = ModuleProgress.objects.filter(module=module).aggregate(
        total_users=Count('user', distinct=True),
        completed_users=Count('user', filter=Q(is_completed=True), distinct=True)
    )
    
    stats_data = {
        'module': {
            'id': module.id,
            'number': module.number,
            'title': module.title
        },
        'quiz_stats': quiz_stats if not module.is_reporting_module else None,
        'audio_stats': audio_stats,
        'completion_rate': completion_rate if not module.is_reporting_module else None
    }
    
    return Response(stats_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def intro_content(request):
    """Vue pour récupérer le contenu d'introduction selon la langue"""
    
    user = request.user
    language = user.preferred_language
    
    intro_content = {
        'FR': {
            'title': 'Bienvenue dans la formation parajuridique',
            'content': '''
            Cette application vous permettra d'acquérir les compétences essentielles 
            en tant que parajuriste communautaire. 
            
            ## Structure de la formation :
            
            - **9 modules de formation** avec quiz de validation
            - **1 module de signalement** pour rapporter des cas
            - **Score minimum requis :** 80% pour valider chaque module
            - **Tentatives illimitées** pour chaque quiz
            
            ## Comment progresser :
            
            1. Lisez attentivement le contenu de chaque module
            2. Répondez au quiz de validation
            3. Obtenez au moins 80% pour valider le module
            4. Accédez au module suivant
            5. Obtenez votre attestation une fois tous les modules validés
            
            Bonne formation !
            ''',
            'next_action': 'Commencer les modules'
        },
        'FON': {
            'title': 'Aizo na formation parajuridique tɔn mɛ',
            'content': 'Audio d\'introduction en langue Fon disponible',
            'audio_intro': '/media/intro/intro_fon.mp3',  # À adapter selon vos fichiers
            'next_action': 'Écouter les modules audio'
        }
    }
    
    content = intro_content.get(language, intro_content['FR'])
    
    return Response({
        'language': language,
        'content': content,
        'total_modules': 10,
        'user_language_display': user.get_preferred_language_display()
    })

class ModuleSearchView(generics.ListAPIView):
    """Vue pour rechercher dans les modules"""
    
    serializer_class = ModuleListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Module.objects.filter(is_active=True)
        search_term = self.request.query_params.get('search', None)
        
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(content_fr__icontains=search_term)
            )
        
        return queryset.order_by('number')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_module_status(request):
    """Vue pour obtenir le statut de tous les modules pour l'utilisateur"""
    
    user = request.user
    modules = Module.objects.filter(is_active=True).order_by('number')
    
    module_status = []
    
    for module in modules:
        status_data = {
            'module': ModuleListSerializer(module).data,
            'is_completed': False,
            'best_score': None,
            'total_attempts': 0,
            'can_access': True,  # Selon le cahier des charges, tous les modules sont accessibles
        }
        
        if module.is_reporting_module:
            # Module de signalement - pas de quiz
            status_data['type'] = 'reporting'
        elif user.preferred_language == 'FR':
            # Modules avec quiz pour les utilisateurs français
            attempts = UserQuizAttempt.objects.filter(
                user=user, module=module
            )
            
            if attempts.exists():
                best_attempt = attempts.order_by('-score').first()
                status_data['best_score'] = best_attempt.score
                status_data['is_completed'] = best_attempt.is_passed
                status_data['total_attempts'] = attempts.count()
            
            status_data['type'] = 'quiz'
        else:
            # Modules audio pour les utilisateurs Fon
            from progress.models import ModuleProgress
            try:
                progress = ModuleProgress.objects.get(user=user, module=module)
                status_data['is_completed'] = progress.is_completed
                status_data['progress_percentage'] = progress.progress_percentage
            except ModuleProgress.DoesNotExist:
                status_data['progress_percentage'] = 0
            
            status_data['type'] = 'audio'
        
        module_status.append(status_data)
    
    return Response({
        'user_language': user.preferred_language,
        'modules': module_status
    })