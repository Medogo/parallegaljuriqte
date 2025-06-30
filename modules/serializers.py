# modules/serializers.py
from rest_framework import serializers
from .models import (
    Module, QuizQuestion, AnswerChoice, 
    UserQuizAttempt, UserQuizAnswer
)

class AnswerChoiceSerializer(serializers.ModelSerializer):
    """Serializer pour les choix de réponse"""
    
    class Meta:
        model = AnswerChoice
        fields = ['id', 'choice_text', 'order']
        # is_correct est exclu pour ne pas révéler les bonnes réponses

class AnswerChoiceWithCorrectSerializer(serializers.ModelSerializer):
    """Serializer pour les choix de réponse avec indication de correction"""
    
    class Meta:
        model = AnswerChoice
        fields = ['id', 'choice_text', 'is_correct', 'order']

class QuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer pour les questions de quiz"""
    
    answer_choices = AnswerChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'order', 'question_type', 'question_text',
            'points', 'answer_choices'
        ]

class QuizQuestionWithAnswersSerializer(serializers.ModelSerializer):
    """Serializer pour les questions avec les bonnes réponses (après soumission)"""
    
    answer_choices = AnswerChoiceWithCorrectSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'order', 'question_type', 'question_text',
            'explanation', 'points', 'answer_choices'
        ]

class ModuleListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des modules"""
    
    is_reporting_module = serializers.ReadOnlyField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'number', 'title', 'description',
            'is_reporting_module', 'audio_duration'
        ]

class ModuleDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail d'un module"""
    
    quiz_questions = QuizQuestionSerializer(many=True, read_only=True)
    is_reporting_module = serializers.ReadOnlyField()
    has_audio = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'number', 'title', 'description',
            'introduction_fr', 'objectives_fr', 'key_concepts_fr',
            'content_fr', 'audio_fon', 'audio_duration',
            'is_reporting_module', 'has_audio', 'quiz_questions'
        ]
    
    def get_has_audio(self, obj):
        """Vérifie si le module a un fichier audio"""
        return bool(obj.audio_fon)
    
    def to_representation(self, instance):
        """Personnalise la représentation selon la langue de l'utilisateur"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user_language = request.user.preferred_language
            
            # Si l'utilisateur préfère le Fon, on ne retourne que les infos nécessaires
            if user_language == 'FON':
                # Pour les utilisateurs Fon, on garde seulement les infos essentielles
                fon_data = {
                    'id': data['id'],
                    'number': data['number'],
                    'title': data['title'],
                    'description': data['description'],
                    'audio_fon': data['audio_fon'],
                    'audio_duration': data['audio_duration'],
                    'has_audio': data['has_audio'],
                    'is_reporting_module': data['is_reporting_module']
                }
                return fon_data
        
        return data

class UserQuizAnswerSerializer(serializers.ModelSerializer):
    """Serializer pour les réponses d'un utilisateur"""
    
    selected_choices = serializers.PrimaryKeyRelatedField(
        queryset=AnswerChoice.objects.all(),
        many=True
    )
    question = serializers.PrimaryKeyRelatedField(
        queryset=QuizQuestion.objects.all()
    )
    
    class Meta:
        model = UserQuizAnswer
        fields = ['question', 'selected_choices']

class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer pour la soumission d'un quiz"""
    
    module_id = serializers.IntegerField()
    answers = UserQuizAnswerSerializer(many=True)
    started_at = serializers.DateTimeField()
    
    def validate_module_id(self, value):
        """Valide que le module existe et est actif"""
        try:
            module = Module.objects.get(id=value, is_active=True)
            if module.is_reporting_module:
                raise serializers.ValidationError(
                    "Le module de signalement n'a pas de quiz."
                )
            return value
        except Module.DoesNotExist:
            raise serializers.ValidationError("Module introuvable.")
    
    def validate_answers(self, value):
        """Valide les réponses soumises"""
        if not value:
            raise serializers.ValidationError("Au moins une réponse est requise.")
        
        # Vérifier que toutes les questions ont une réponse
        question_ids = set(answer['question'].id for answer in value)
        
        # Vérifier la cohérence des choix de réponse
        for answer in value:
            question = answer['question']
            selected_choices = answer['selected_choices']
            
            # Vérifier que les choix appartiennent à la question
            valid_choice_ids = set(
                question.answer_choices.values_list('id', flat=True)
            )
            selected_choice_ids = set(choice.id for choice in selected_choices)
            
            if not selected_choice_ids.issubset(valid_choice_ids):
                raise serializers.ValidationError(
                    f"Choix invalides pour la question {question.order}"
                )
            
            # Vérifier le type de question
            if question.question_type == 'SINGLE' and len(selected_choices) > 1:
                raise serializers.ValidationError(
                    f"La question {question.order} n'accepte qu'une seule réponse"
                )
        
        return value

class UserQuizAttemptSerializer(serializers.ModelSerializer):
    """Serializer pour les tentatives de quiz"""
    
    module_title = serializers.CharField(source='module.title', read_only=True)
    module_number = serializers.IntegerField(source='module.number', read_only=True)
    
    class Meta:
        model = UserQuizAttempt
        fields = [
            'id', 'module_number', 'module_title', 'attempt_number',
            'score', 'total_questions', 'correct_answers',
            'time_taken', 'is_passed', 'started_at', 'completed_at'
        ]

class QuizResultSerializer(serializers.Serializer):
    """Serializer pour les résultats d'un quiz"""
    
    attempt = UserQuizAttemptSerializer()
    questions_with_answers = QuizQuestionWithAnswersSerializer(many=True)
    user_answers = serializers.DictField()
    passed = serializers.BooleanField()
    message = serializers.CharField()

class AudioProgressSerializer(serializers.Serializer):
    """Serializer pour le suivi de la progression audio"""
    
    module_id = serializers.IntegerField()
    progress_percentage = serializers.FloatField(min_value=0, max_value=100)
    current_time = serializers.IntegerField(min_value=0)
    
    def validate_module_id(self, value):
        """Valide que le module existe et a un audio"""
        try:
            module = Module.objects.get(id=value, is_active=True)
            if not module.audio_fon:
                raise serializers.ValidationError(
                    "Ce module n'a pas de fichier audio."
                )
            return value
        except Module.DoesNotExist:
            raise serializers.ValidationError("Module introuvable.")

class ModuleStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'un module"""
    
    total_users = serializers.IntegerField()
    completed_users = serializers.IntegerField()
    average_score = serializers.FloatField()
    completion_rate = serializers.FloatField()
    average_attempts = serializers.FloatField()