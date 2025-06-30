# progress/serializers.py
from rest_framework import serializers
from .models import ModuleProgress, Certificate, OverallProgress, UserActivity
from modules.models import Module

class ModuleProgressSerializer(serializers.ModelSerializer):
    """Serializer pour la progression des modules"""
    
    module_number = serializers.IntegerField(source='module.number', read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True)
    is_quiz_based = serializers.ReadOnlyField()
    is_audio_based = serializers.ReadOnlyField()
    
    class Meta:
        model = ModuleProgress
        fields = [
            'id', 'module_number', 'module_title', 'progress_percentage',
            'is_completed', 'last_audio_position', 'total_listening_time',
            'listening_sessions', 'is_quiz_based', 'is_audio_based',
            'started_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'started_at', 'updated_at', 'completed_at',
            'total_listening_time', 'listening_sessions'
        ]

class CertificateSerializer(serializers.ModelSerializer):
    """Serializer pour les certificats"""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_commune = serializers.CharField(source='user.commune', read_only=True)
    verification_url = serializers.SerializerMethodField()
    can_download = serializers.ReadOnlyField(source='can_download_pdf')
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'verification_code', 'full_name',
            'user_name', 'user_phone', 'user_commune', 'completion_date',
            'total_modules_completed', 'average_score', 'certificate_file',
            'is_valid', 'signed_by', 'signature_date', 'verification_url',
            'can_download'
        ]
        read_only_fields = [
            'certificate_id', 'verification_code', 'completion_date',
            'is_valid', 'signed_by', 'signature_date'
        ]
    
    def get_verification_url(self, obj):
        """Génère l'URL de vérification du certificat"""
        return obj.generate_verification_url()

class CertificateRequestSerializer(serializers.Serializer):
    """Serializer pour la demande de certificat"""
    
    full_name = serializers.CharField(
        max_length=100,
        help_text="Nom complet pour le certificat"
    )
    
    def validate(self, attrs):
        """Valide que l'utilisateur peut obtenir un certificat"""
        user = self.context['request'].user
        
        # Vérifier que l'utilisateur a terminé tous les modules
        if user.preferred_language == 'FR':
            # Pour les utilisateurs français - vérifier les quiz
            from modules.models import UserQuizAttempt
            
            training_modules = Module.objects.filter(is_active=True, number__lt=10)
            passed_modules = UserQuizAttempt.objects.filter(
                user=user,
                module__in=training_modules,
                is_passed=True
            ).values_list('module', flat=True).distinct()
            
            if len(passed_modules) < training_modules.count():
                raise serializers.ValidationError(
                    "Vous devez valider tous les modules avant de demander l'attestation."
                )
        
        else:
            # Pour les utilisateurs Fon - ils ne peuvent pas obtenir l'attestation automatiquement
            raise serializers.ValidationError(
                "Les utilisateurs en langue Fon doivent passer l'examen au siège de HAI pour obtenir leur attestation."
            )
        
        return attrs

class OverallProgressSerializer(serializers.ModelSerializer):
    """Serializer pour la progression globale"""
    
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_language = serializers.CharField(source='user.preferred_language', read_only=True)
    next_module = serializers.SerializerMethodField()
    
    class Meta:
        model = OverallProgress
        fields = [
            'id', 'user_name', 'user_language', 'total_modules',
            'completed_modules', 'completion_percentage', 'total_quiz_attempts',
            'average_quiz_score', 'total_audio_time', 'can_get_certificate',
            'certificate_requested', 'next_module', 'started_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'total_modules', 'completed_modules', 'completion_percentage',
            'total_quiz_attempts', 'average_quiz_score', 'total_audio_time',
            'can_get_certificate', 'started_at', 'updated_at', 'completed_at'
        ]
    
    def get_next_module(self, obj):
        """Retourne le prochain module à compléter"""
        next_module = obj.get_next_module()
        if next_module:
            return {
                'id': next_module.id,
                'number': next_module.number,
                'title': next_module.title
            }
        return None

class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer pour les activités utilisateur"""
    
    module_title = serializers.CharField(source='module.title', read_only=True, allow_null=True)
    activity_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'activity_type', 'activity_display', 'module',
            'module_title', 'details', 'timestamp'
        ]
        read_only_fields = ['timestamp']

class ActivityCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une activité"""
    
    class Meta:
        model = UserActivity
        fields = ['activity_type', 'module', 'details']
    
    def create(self, validated_data):
        """Crée une nouvelle activité avec l'utilisateur de la requête"""
        validated_data['user'] = self.context['request'].user
        
        # Ajouter des informations de session si disponibles
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return super().create(validated_data)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ProgressSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé de progression"""
    
    overall_progress = OverallProgressSerializer()
    module_progress = ModuleProgressSerializer(many=True)
    recent_activities = UserActivitySerializer(many=True)
    certificates = CertificateSerializer(many=True)
    
    # Statistiques additionnelles
    total_time_spent = serializers.IntegerField()
    days_since_start = serializers.IntegerField()
    last_activity_date = serializers.DateTimeField()
    modules_this_week = serializers.IntegerField()

class LeaderboardSerializer(serializers.Serializer):
    """Serializer pour le classement (anonymisé)"""
    
    rank = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    average_score = serializers.FloatField(allow_null=True)
    completed_modules = serializers.IntegerField()
    commune = serializers.CharField()
    is_current_user = serializers.BooleanField()

class ProgressStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques globales de progression"""
    
    total_users = serializers.IntegerField()
    active_users_week = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    average_completion_time = serializers.FloatField()
    top_communes = serializers.ListField()
    module_completion_rates = serializers.DictField()
    
    # Répartition par langue
    french_users = serializers.IntegerField()
    fon_users = serializers.IntegerField()
    
    # Certificats
    total_certificates = serializers.IntegerField()
    certificates_this_month = serializers.IntegerField()

class CertificateVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification de certificat"""
    
    verification_code = serializers.CharField(max_length=20)
    
    def validate_verification_code(self, value):
        """Valide le code de vérification"""
        try:
            certificate = Certificate.objects.get(
                verification_code=value,
                is_valid=True
            )
            return value
        except Certificate.DoesNotExist:
            raise serializers.ValidationError(
                "Code de vérification invalide ou certificat non trouvé."
            )

class FonUserProgressSerializer(serializers.Serializer):
    """Serializer spécial pour les utilisateurs Fon"""
    
    message = serializers.CharField()
    contact_info = serializers.DictField()
    progress_screenshot_required = serializers.BooleanField()
    whatsapp_number = serializers.CharField()
    
    def to_representation(self, instance):
        """Génère le message pour les utilisateurs Fon"""
        user = instance
        
        # Vérifier si tous les modules audio sont terminés
        from modules.models import Module
        training_modules = Module.objects.filter(is_active=True, number__lt=10)
        completed_modules = ModuleProgress.objects.filter(
            user=user,
            module__in=training_modules,
            is_completed=True
        ).count()
        
        if completed_modules == training_modules.count():
            message = (
                "Félicitations ! Vous avez terminé tous les modules audio. "
                "Pour obtenir votre attestation, vous devez passer l'examen "
                "au siège de HAI ou dans une annexe. Envoyez une capture "
                "d'écran de votre progression à 100% avec vos informations "
                "(nom, prénom, lieu de résidence) au numéro WhatsApp ci-dessous."
            )
            screenshot_required = True
        else:
            message = (
                f"Vous avez terminé {completed_modules}/{training_modules.count()} modules. "
                "Continuez votre formation pour être éligible à l'attestation."
            )
            screenshot_required = False
        
        return {
            'message': message,
            'contact_info': {
                'whatsapp_number': '+229 01 57 57 51 67',
                'organization': 'HAI (Human Rights and Advocacy Initiative)',
                'required_info': [
                    'Nom complet',
                    'Lieu de résidence',
                    'Capture d\'écran de progression 100%'
                ]
            },
            'progress_screenshot_required': screenshot_required,
            'whatsapp_number': '+229 01 57 57 51 67',
            'completion_status': {
                'completed_modules': completed_modules,
                'total_modules': training_modules.count(),
                'is_eligible': completed_modules == training_modules.count()
            }
        }