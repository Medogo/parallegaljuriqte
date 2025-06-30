# reporting/serializers.py
from rest_framework import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import CommunityReport, ReportAttachment, AudioReport, ReportFollowUp
from datetime import date, timedelta

class ReportAttachmentSerializer(serializers.ModelSerializer):
    """Serializer pour les pièces jointes"""
    
    file_size_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = ReportAttachment
        fields = [
            'id', 'filename', 'file_size', 'file_size_formatted',
            'description', 'uploaded_at', 'file'
        ]
        read_only_fields = ['filename', 'file_size', 'uploaded_at']

class CommunityReportCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un signalement communautaire"""
    
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True,
        help_text="Liste des fichiers à joindre (max 5 fichiers, 10MB chacun)"
    )
    
    class Meta:
        model = CommunityReport
        fields = [
            'problem_type', 'title', 'description', 'location',
            'commune', 'incident_date', 'incident_time',
            'is_anonymous', 'contact_allowed', 'attachments'
        ]
    
    def validate_incident_date(self, value):
        """Valide que la date d'incident n'est pas dans le futur"""
        if value > date.today():
            raise serializers.ValidationError(
                "La date de l'incident ne peut pas être dans le futur."
            )
        
        # Vérifier que la date n'est pas trop ancienne (plus de 10 ans)
        ten_years_ago = date.today() - timedelta(days=365 * 10)
        if value < ten_years_ago:
            raise serializers.ValidationError(
                "La date de l'incident semble trop ancienne. Veuillez vérifier."
            )
        
        return value
    
    def validate_attachments(self, value):
        """Valide les pièces jointes"""
        if len(value) > 5:
            raise serializers.ValidationError(
                "Maximum 5 fichiers autorisés."
            )
        
        allowed_types = ['image/jpeg', 'image/png', 'application/pdf', 
                        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        max_size = 10 * 1024 * 1024  # 10MB
        
        for file in value:
            if file.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Type de fichier non autorisé: {file.content_type}. "
                    "Seuls les formats JPG, PNG, PDF, DOC, DOCX sont acceptés."
                )
            
            if file.size > max_size:
                raise serializers.ValidationError(
                    f"Le fichier {file.name} est trop volumineux (max 10MB)."
                )
        
        return value
    
    def create(self, validated_data):
        """Crée un signalement avec ses pièces jointes"""
        attachments_data = validated_data.pop('attachments', [])
        
        # Créer le signalement
        report = CommunityReport.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        
        # Créer les pièces jointes
        for attachment_file in attachments_data:
            ReportAttachment.objects.create(
                report=report,
                file=attachment_file,
                description=f"Pièce jointe: {attachment_file.name}"
            )
        
        return report

class CommunityReportSerializer(serializers.ModelSerializer):
    """Serializer pour afficher un signalement communautaire"""
    
    attachments = ReportAttachmentSerializer(many=True, read_only=True)
    reporter_info = serializers.ReadOnlyField()
    problem_type_display = serializers.CharField(source='get_problem_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_level_display', read_only=True)
    can_be_contacted = serializers.ReadOnlyField()
    
    class Meta:
        model = CommunityReport
        fields = [
            'id', 'report_id', 'problem_type', 'problem_type_display',
            'title', 'description', 'location', 'commune',
            'incident_date', 'incident_time', 'is_anonymous',
            'contact_allowed', 'status', 'status_display',
            'priority_level', 'priority_display', 'reporter_info',
            'can_be_contacted', 'attachments', 'created_at',
            'updated_at', 'assigned_to', 'resolution_notes',
            'resolved_at'
        ]
        read_only_fields = [
            'id', 'report_id', 'reporter_info', 'can_be_contacted',
            'created_at', 'updated_at', 'assigned_to', 'resolution_notes',
            'resolved_at'
        ]

class AudioReportCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un signalement audio"""
    
    class Meta:
        model = AudioReport
        fields = [
            'audio_file', 'duration', 'consent_given', 'is_anonymous'
        ]
    
    def validate_audio_file(self, value):
        """Valide le fichier audio"""
        # Vérifier la taille (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "Le fichier audio est trop volumineux (max 50MB)."
            )
        
        # Vérifier le type de fichier
        allowed_types = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/aac']
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Type de fichier non autorisé: {value.content_type}. "
                "Seuls les formats MP3, WAV, M4A, AAC sont acceptés."
            )
        
        return value
    
    def validate_duration(self, value):
        """Valide la durée de l'audio"""
        if value > 180:  # 3 minutes max
            raise serializers.ValidationError(
                "L'enregistrement ne peut pas dépasser 3 minutes."
            )
        
        if value < 5:  # 5 secondes min
            raise serializers.ValidationError(
                "L'enregistrement doit durer au moins 5 secondes."
            )
        
        return value
    
    def validate_consent_given(self, value):
        """Valide que le consentement a été donné"""
        if not value:
            raise serializers.ValidationError(
                "Vous devez donner votre consentement pour transmettre l'audio aux structures partenaires."
            )
        return value
    
    def create(self, validated_data):
        """Crée un signalement audio"""
        return AudioReport.objects.create(
            user=self.context['request'].user,
            file_size=validated_data['audio_file'].size,
            **validated_data
        )

class AudioReportSerializer(serializers.ModelSerializer):
    """Serializer pour afficher un signalement audio"""
    
    reporter_info = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    file_size_formatted = serializers.ReadOnlyField()
    extracted_problem_type_display = serializers.CharField(
        source='get_extracted_problem_type_display', 
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = AudioReport
        fields = [
            'id', 'report_id', 'audio_file', 'duration', 'duration_formatted',
            'file_size', 'file_size_formatted', 'consent_given', 'is_anonymous',
            'status', 'status_display', 'transcription', 'transcribed_by',
            'transcribed_at', 'extracted_problem_type', 'extracted_problem_type_display',
            'extracted_location', 'reporter_info', 'created_at', 'updated_at',
            'admin_notes', 'assigned_to'
        ]
        read_only_fields = [
            'id', 'report_id', 'file_size', 'reporter_info', 'transcription',
            'transcribed_by', 'transcribed_at', 'extracted_problem_type',
            'extracted_location', 'created_at', 'updated_at', 'admin_notes',
            'assigned_to'
        ]

class ReportFollowUpSerializer(serializers.ModelSerializer):
    """Serializer pour les suivis de signalements"""
    
    update_type_display = serializers.CharField(source='get_update_type_display', read_only=True)
    
    class Meta:
        model = ReportFollowUp
        fields = [
            'id', 'update_type', 'update_type_display', 'message',
            'author', 'is_public', 'created_at'
        ]
        read_only_fields = ['created_at']

class ReportStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de signalements"""
    
    total_reports = serializers.IntegerField()
    text_reports = serializers.IntegerField()
    audio_reports = serializers.IntegerField()
    
    # Par statut
    pending_reports = serializers.IntegerField()
    under_review_reports = serializers.IntegerField()
    resolved_reports = serializers.IntegerField()
    
    # Par type de problème
    justice_reports = serializers.IntegerField()
    health_reports = serializers.IntegerField()
    other_reports = serializers.IntegerField()
    
    # Par période
    reports_this_week = serializers.IntegerField()
    reports_this_month = serializers.IntegerField()
    
    # Taux de résolution
    resolution_rate = serializers.FloatField()
    average_resolution_time = serializers.FloatField()

class UserReportSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des signalements d'un utilisateur"""
    
    total_reports = serializers.IntegerField()
    text_reports = CommunityReportSerializer(many=True)
    audio_reports = AudioReportSerializer(many=True)
    
    # Statistiques
    pending_count = serializers.IntegerField()
    resolved_count = serializers.IntegerField()
    last_report_date = serializers.DateTimeField(allow_null=True)

class ReportSearchSerializer(serializers.Serializer):
    """Serializer pour la recherche de signalements"""
    
    search = serializers.CharField(required=False, allow_blank=True)
    problem_type = serializers.ChoiceField(
        choices=CommunityReport.PROBLEM_TYPES,
        required=False,
        allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=CommunityReport.STATUS_CHOICES,
        required=False,
        allow_blank=True
    )
    commune = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    
    def validate(self, attrs):
        """Valide les paramètres de recherche"""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise serializers.ValidationError({
                    'date_from': 'La date de début ne peut pas être postérieure à la date de fin.'
                })
        
        return attrs