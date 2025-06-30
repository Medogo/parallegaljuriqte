# progress/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from authentication.models import CustomUser
from modules.models import Module
from django.utils import timezone
import uuid

class ModuleProgress(models.Model):
    """Modèle pour suivre la progression des utilisateurs dans les modules"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='module_progress',
        verbose_name="Utilisateur"
    )
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name="Module"
    )
    
    # Progression générale
    progress_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Pourcentage de progression"
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Module terminé"
    )
    
    # Spécifique à l'audio (pour les utilisateurs Fon)
    last_audio_position = models.PositiveIntegerField(
        default=0,
        verbose_name="Dernière position audio (secondes)"
    )
    
    total_listening_time = models.PositiveIntegerField(
        default=0,
        verbose_name="Temps total d'écoute (secondes)"
    )
    
    listening_sessions = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de sessions d'écoute"
    )
    
    # Dates
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Commencé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Terminé le"
    )
    
    class Meta:
        unique_together = ['user', 'module']
        ordering = ['user', 'module__number']
        verbose_name = "Progression de module"
        verbose_name_plural = "Progressions de modules"
    
    def __str__(self):
        return f"{self.user.full_name} - Module {self.module.number} ({self.progress_percentage}%)"
    
    def save(self, *args, **kwargs):
        # Marquer la date de completion si le module vient d'être terminé
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        
        super().save(*args, **kwargs)
    
    @property
    def is_quiz_based(self):
        """Vérifie si la progression est basée sur un quiz (utilisateurs français)"""
        return self.user.preferred_language == 'FR' and not self.module.is_reporting_module
    
    @property
    def is_audio_based(self):
        """Vérifie si la progression est basée sur l'audio (utilisateurs Fon)"""
        return self.user.preferred_language == 'FON' and not self.module.is_reporting_module

class Certificate(models.Model):
    """Modèle pour les attestations de formation"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name="Utilisateur"
    )
    
    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="ID unique du certificat"
    )
    
    verification_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code de vérification"
    )
    
    # Détails de l'attestation
    full_name = models.CharField(
        max_length=100,
        verbose_name="Nom complet",
        help_text="Nom au moment de l'obtention"
    )
    
    completion_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'obtention"
    )
    
    total_modules_completed = models.PositiveIntegerField(
        verbose_name="Modules terminés"
    )
    
    average_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Score moyen",
        help_text="Score moyen pour les utilisateurs français"
    )
    
    # Fichier PDF de l'attestation
    certificate_file = models.FileField(
        upload_to='certificates/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Fichier PDF de l'attestation"
    )
    
    # Statut
    is_valid = models.BooleanField(
        default=True,
        verbose_name="Attestation valide"
    )
    
    # Informations de signature/validation
    signed_by = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Signé par"
    )
    
    signature_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de signature"
    )
    
    class Meta:
        ordering = ['-completion_date']
        verbose_name = "Certificat"
        verbose_name_plural = "Certificats"
    
    def __str__(self):
        return f"Certificat de {self.full_name} - {self.verification_code}"
    
    def save(self, *args, **kwargs):
        # Générer un code de vérification si pas encore défini
        if not self.verification_code:
            import random
            import string
            self.verification_code = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=12)
            )
        
        # Copier le nom complet de l'utilisateur
        if not self.full_name:
            self.full_name = self.user.full_name
        
        super().save(*args, **kwargs)
    
    @property
    def can_download_pdf(self):
        """Vérifie si le PDF peut être téléchargé"""
        return bool(self.certificate_file) and self.is_valid
    
    def generate_verification_url(self):
        """Génère l'URL de vérification du certificat"""
        # Cette URL sera implémentée selon votre domaine
        return f"https://yourapp.com/verify/{self.verification_code}"

class UserActivity(models.Model):
    """Modèle pour suivre l'activité des utilisateurs"""
    
    ACTIVITY_TYPES = [
        ('LOGIN', 'Connexion'),
        ('MODULE_VIEW', 'Consultation de module'),
        ('QUIZ_START', 'Début de quiz'),
        ('QUIZ_SUBMIT', 'Soumission de quiz'),
        ('AUDIO_PLAY', 'Lecture audio'),
        ('AUDIO_PAUSE', 'Pause audio'),
        ('AUDIO_COMPLETE', 'Audio terminé'),
        ('CERTIFICATE_REQUEST', 'Demande d\'attestation'),
        ('CERTIFICATE_DOWNLOAD', 'Téléchargement d\'attestation'),
        ('REPORT_SUBMIT', 'Soumission de signalement'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Utilisateur"
    )
    
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        verbose_name="Type d'activité"
    )
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Module concerné"
    )
    
    details = models.JSONField(
        default=dict,
        verbose_name="Détails de l'activité"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage"
    )
    
    # Informations de session
    session_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID de session"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="Adresse IP"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Activité utilisateur"
        verbose_name_plural = "Activités utilisateur"
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_activity_type_display()} - {self.timestamp}"

class OverallProgress(models.Model):
    """Modèle pour la progression globale d'un utilisateur"""
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='overall_progress',
        verbose_name="Utilisateur"
    )
    
    # Progression générale
    total_modules = models.PositiveIntegerField(
        default=10,
        verbose_name="Nombre total de modules"
    )
    
    completed_modules = models.PositiveIntegerField(
        default=0,
        verbose_name="Modules terminés"
    )
    
    completion_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Pourcentage de completion global"
    )
    
    # Statistiques spécifiques par langue
    total_quiz_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="Tentatives de quiz total"
    )
    
    average_quiz_score = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Score moyen aux quiz"
    )
    
    total_audio_time = models.PositiveIntegerField(
        default=0,
        verbose_name="Temps d'écoute total (secondes)"
    )
    
    # Éligibilité à l'attestation
    can_get_certificate = models.BooleanField(
        default=False,
        verbose_name="Éligible à l'attestation"
    )
    
    certificate_requested = models.BooleanField(
        default=False,
        verbose_name="Attestation demandée"
    )
    
    # Dates importantes
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Formation commencée le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Formation terminée le"
    )
    
    class Meta:
        verbose_name = "Progression globale"
        verbose_name_plural = "Progressions globales"
    
    def __str__(self):
        return f"{self.user.full_name} - {self.completion_percentage}% complété"
    
    def update_progress(self):
        """Met à jour la progression globale basée sur les progressions des modules"""
        # Compter les modules terminés (excluant le module de signalement)
        training_modules = Module.objects.filter(is_active=True, number__lt=10)
        completed_count = 0
        
        if self.user.preferred_language == 'FR':
            # Pour les utilisateurs français, compter les modules avec quiz réussi
            from modules.models import UserQuizAttempt
            
            passed_modules = UserQuizAttempt.objects.filter(
                user=self.user,
                module__in=training_modules,
                is_passed=True
            ).values_list('module', flat=True).distinct()
            
            completed_count = len(passed_modules)
            
            # Calculer le score moyen
            attempts = UserQuizAttempt.objects.filter(
                user=self.user,
                module__in=training_modules
            )
            if attempts.exists():
                # Prendre la meilleure tentative par module
                best_attempts = []
                for module in training_modules:
                    best = attempts.filter(module=module).order_by('-score').first()
                    if best:
                        best_attempts.append(best.score)
                
                if best_attempts:
                    self.average_quiz_score = sum(best_attempts) / len(best_attempts)
            
            self.total_quiz_attempts = attempts.count()
        
        else:
            # Pour les utilisateurs Fon, compter les modules audio terminés
            completed_progress = ModuleProgress.objects.filter(
                user=self.user,
                module__in=training_modules,
                is_completed=True
            )
            completed_count = completed_progress.count()
            
            # Calculer le temps d'écoute total
            total_time = ModuleProgress.objects.filter(
                user=self.user
            ).aggregate(
                total=models.Sum('total_listening_time')
            )['total'] or 0
            
            self.total_audio_time = total_time
        
        # Mettre à jour les compteurs
        self.completed_modules = completed_count
        self.total_modules = training_modules.count()
        
        if self.total_modules > 0:
            self.completion_percentage = (completed_count / self.total_modules) * 100
        
        # Vérifier l'éligibilité à l'attestation
        self.can_get_certificate = completed_count == self.total_modules
        
        if self.can_get_certificate and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.save()
    
    def get_next_module(self):
        """Retourne le prochain module à compléter"""
        if self.user.preferred_language == 'FR':
            # Pour les utilisateurs français
            from modules.models import UserQuizAttempt
            
            passed_modules = UserQuizAttempt.objects.filter(
                user=self.user,
                is_passed=True
            ).values_list('module__number', flat=True)
            
            next_module = Module.objects.filter(
                is_active=True,
                number__lt=10  # Exclure le module de signalement
            ).exclude(number__in=passed_modules).order_by('number').first()
            
        else:
            # Pour les utilisateurs Fon
            completed_modules = ModuleProgress.objects.filter(
                user=self.user,
                is_completed=True
            ).values_list('module__number', flat=True)
            
            next_module = Module.objects.filter(
                is_active=True,
                number__lt=10  # Exclure le module de signalement
            ).exclude(number__in=completed_modules).order_by('number').first()
        
        return next_module