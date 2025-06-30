# reporting/models.py
from django.db import models
from django.core.validators import FileExtensionValidator
from authentication.models import CustomUser
import uuid
import os

def report_attachment_upload_path(instance, filename):
    """Chemin de téléchargement pour les pièces jointes des signalements"""
    return f'reports/{instance.report.id}/attachments/{filename}'

def audio_report_upload_path(instance, filename):
    """Chemin de téléchargement pour les signalements audio"""
    return f'reports/audio/{instance.id}/{filename}'

class CommunityReport(models.Model):
    """Modèle pour les signalements communautaires"""
    
    PROBLEM_TYPES = [
        ('JUSTICE', 'Justice'),
        ('HEALTH', 'Santé'),
        ('OTHER', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('UNDER_REVIEW', 'En cours d\'examen'),
        ('PROCESSED', 'Traité'),
        ('RESOLVED', 'Résolu'),
        ('CLOSED', 'Fermé'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Élevée'),
        ('URGENT', 'Urgente'),
    ]
    
    # Identifiant unique
    report_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="ID du signalement"
    )
    
    # Utilisateur
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='community_reports',
        verbose_name="Utilisateur"
    )
    
    # Informations du signalement
    problem_type = models.CharField(
        max_length=10,
        choices=PROBLEM_TYPES,
        verbose_name="Type de problème"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Titre du signalement",
        help_text="Résumé court du problème"
    )
    
    description = models.TextField(
        verbose_name="Description détaillée",
        help_text="Description complète de la situation"
    )
    
    # Localisation
    location = models.CharField(
        max_length=200,
        verbose_name="Lieu de l'incident",
        help_text="Adresse ou description du lieu"
    )
    
    commune = models.CharField(
        max_length=100,
        verbose_name="Commune",
        help_text="Commune où s'est produit l'incident"
    )
    
    # Date de l'incident
    incident_date = models.DateField(
        verbose_name="Date de l'incident"
    )
    
    incident_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Heure de l'incident"
    )
    
    # Options d'anonymat et de contact
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name="Signalement anonyme"
    )
    
    contact_allowed = models.BooleanField(
        default=True,
        verbose_name="Autorisation de contact",
        help_text="Accepte d'être contacté par les autorités"
    )
    
    # Gestion du signalement
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    
    priority_level = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='MEDIUM',
        verbose_name="Niveau de priorité"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    # Suivi administratif
    assigned_to = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Assigné à",
        help_text="Personne ou organisation en charge"
    )
    
    admin_notes = models.TextField(
        blank=True,
        verbose_name="Notes administratives",
        help_text="Notes internes pour le suivi"
    )
    
    resolution_notes = models.TextField(
        blank=True,
        verbose_name="Notes de résolution",
        help_text="Détails sur la résolution du cas"
    )
    
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de résolution"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Signalement communautaire"
        verbose_name_plural = "Signalements communautaires"
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['problem_type', 'commune']),
            models.Index(fields=['priority_level', 'status']),
        ]
    
    def __str__(self):
        anonymous_text = " (Anonyme)" if self.is_anonymous else ""
        return f"{self.get_problem_type_display()} - {self.title}{anonymous_text}"
    
    @property
    def reporter_info(self):
        """Retourne les informations du rapporteur selon le niveau d'anonymat"""
        if self.is_anonymous:
            return {
                'name': 'Anonyme',
                'phone': 'Non divulgué',
                'commune': self.user.commune
            }
        else:
            return {
                'name': self.user.full_name,
                'phone': self.user.phone_number,
                'commune': self.user.commune
            }
    
    def can_be_contacted(self):
        """Vérifie si le rapporteur peut être contacté"""
        return not self.is_anonymous and self.contact_allowed

class ReportAttachment(models.Model):
    """Modèle pour les pièces jointes des signalements"""
    
    report = models.ForeignKey(
        CommunityReport,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="Signalement"
    )
    
    file = models.FileField(
        upload_to=report_attachment_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
        )],
        verbose_name="Fichier"
    )
    
    filename = models.CharField(
        max_length=255,
        verbose_name="Nom du fichier"
    )
    
    file_size = models.PositiveIntegerField(
        verbose_name="Taille du fichier (bytes)"
    )
    
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Description de la pièce jointe"
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Téléchargé le"
    )
    
    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
    
    def __str__(self):
        return f"{self.filename} - {self.report.title}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)

class AudioReport(models.Model):
    """Modèle pour les signalements audio (utilisateurs Fon)"""
    
    # Identifiant unique
    report_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="ID du signalement audio"
    )
    
    # Utilisateur
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='audio_reports',
        verbose_name="Utilisateur"
    )
    
    # Fichier audio
    audio_file = models.FileField(
        upload_to=audio_report_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=['mp3', 'wav', 'm4a', 'aac']
        )],
        verbose_name="Fichier audio"
    )
    
    # Métadonnées audio
    duration = models.PositiveIntegerField(
        verbose_name="Durée (secondes)",
        help_text="Durée de l'enregistrement en secondes"
    )
    
    file_size = models.PositiveIntegerField(
        verbose_name="Taille du fichier (bytes)"
    )
    
    # Consentement
    consent_given = models.BooleanField(
        default=False,
        verbose_name="Consentement donné",
        help_text="Consent à transmettre l'audio aux structures partenaires"
    )
    
    # Options d'anonymat
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name="Signalement anonyme"
    )
    
    # Statut
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('TRANSCRIBED', 'Transcrit'),
        ('UNDER_REVIEW', 'En cours d\'examen'),
        ('PROCESSED', 'Traité'),
        ('RESOLVED', 'Résolu'),
        ('CLOSED', 'Fermé'),
    ]
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    
    # Transcription (si disponible)
    transcription = models.TextField(
        blank=True,
        verbose_name="Transcription",
        help_text="Transcription du contenu audio"
    )
    
    transcribed_by = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Transcrit par"
    )
    
    transcribed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de transcription"
    )
    
    # Informations extraites de la transcription
    extracted_problem_type = models.CharField(
        max_length=10,
        choices=CommunityReport.PROBLEM_TYPES,
        blank=True,
        verbose_name="Type de problème identifié"
    )
    
    extracted_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Lieu identifié"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    # Suivi administratif
    admin_notes = models.TextField(
        blank=True,
        verbose_name="Notes administratives"
    )
    
    assigned_to = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Assigné à"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Signalement audio"
        verbose_name_plural = "Signalements audio"
    
    def __str__(self):
        anonymous_text = " (Anonyme)" if self.is_anonymous else ""
        return f"Audio {self.report_id.hex[:8]} - {self.user.full_name}{anonymous_text}"
    
    @property
    def duration_formatted(self):
        """Retourne la durée formatée (mm:ss)"""
        minutes, seconds = divmod(self.duration, 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self):
        """Retourne la taille du fichier formatée"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    @property
    def reporter_info(self):
        """Retourne les informations du rapporteur selon le niveau d'anonymat"""
        if self.is_anonymous:
            return {
                'name': 'Anonyme',
                'phone': 'Non divulgué',
                'commune': self.user.commune
            }
        else:
            return {
                'name': self.user.full_name,
                'phone': self.user.phone_number,
                'commune': self.user.commune
            }

class ReportFollowUp(models.Model):
    """Modèle pour le suivi des signalements"""
    
    # Peut être lié à un signalement textuel ou audio
    text_report = models.ForeignKey(
        CommunityReport,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='follow_ups',
        verbose_name="Signalement textuel"
    )
    
    audio_report = models.ForeignKey(
        AudioReport,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='follow_ups',
        verbose_name="Signalement audio"
    )
    
    # Contenu du suivi
    update_type = models.CharField(
        max_length=20,
        choices=[
            ('STATUS_CHANGE', 'Changement de statut'),
            ('PROGRESS_UPDATE', 'Mise à jour de progression'),
            ('ADDITIONAL_INFO', 'Informations supplémentaires'),
            ('RESOLUTION', 'Résolution'),
            ('CLOSURE', 'Fermeture'),
        ],
        verbose_name="Type de mise à jour"
    )
    
    message = models.TextField(
        verbose_name="Message de suivi"
    )
    
    # Auteur du suivi
    author = models.CharField(
        max_length=100,
        verbose_name="Auteur du suivi"
    )
    
    # Visibilité
    is_public = models.BooleanField(
        default=True,
        verbose_name="Visible par le rapporteur",
        help_text="Si coché, le rapporteur pourra voir cette mise à jour"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Suivi de signalement"
        verbose_name_plural = "Suivis de signalements"
    
    def __str__(self):
        report_ref = (
            f"Text-{self.text_report.report_id.hex[:8]}" if self.text_report 
            else f"Audio-{self.audio_report.report_id.hex[:8]}"
        )
        return f"Suivi {report_ref} - {self.get_update_type_display()}"
    
    def clean(self):
        """Validation pour s'assurer qu'un seul type de signalement est lié"""
        from django.core.exceptions import ValidationError
        
        if not self.text_report and not self.audio_report:
            raise ValidationError(
                "Le suivi doit être lié à un signalement (textuel ou audio)."
            )
        
        if self.text_report and self.audio_report:
            raise ValidationError(
                "Le suivi ne peut être lié qu'à un seul type de signalement."
            )