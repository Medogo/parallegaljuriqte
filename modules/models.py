# modules/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import CustomUser
import uuid
import os

def module_content_upload_path(instance, filename):
    """Chemin de téléchargement pour les contenus de modules"""
    return f'modules/{instance.module.number}/{filename}'

def audio_upload_path(instance, filename):
    """Chemin de téléchargement pour les audios"""
    return f'modules/audio/{instance.number}/{filename}'

class Module(models.Model):
    """Modèle représentant un module de formation"""
    
    number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Numéro du module"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Titre du module"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description du module"
    )
    
    # Contenu français
    introduction_fr = models.TextField(
        verbose_name="Introduction (Français)",
        help_text="Introduction du module en français"
    )
    
    objectives_fr = models.TextField(
        verbose_name="Objectifs pédagogiques (Français)",
        help_text="Objectifs d'apprentissage en français"
    )
    
    key_concepts_fr = models.TextField(
        verbose_name="Notions clés (Français)",
        help_text="Concepts importants à retenir en français"
    )
    
    content_fr = models.TextField(
        verbose_name="Contenu structuré (Français)",
        help_text="Contenu principal du module en français"
    )
    
    # Audio Fon
    audio_fon = models.FileField(
        upload_to=audio_upload_path,
        blank=True,
        null=True,
        verbose_name="Audio Fon",
        help_text="Fichier audio complet en langue Fon"
    )
    
    audio_duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Durée audio (secondes)",
        help_text="Durée de l'audio en secondes"
    )
    
    # Métadonnées
    is_active = models.BooleanField(
        default=True,
        verbose_name="Module actif"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    
    class Meta:
        ordering = ['number']
        verbose_name = "Module"
        verbose_name_plural = "Modules"
    
    def __str__(self):
        return f"Module {self.number}: {self.title}"
    
    @property
    def is_reporting_module(self):
        """Vérifie si c'est le module de signalement (module 10)"""
        return self.number == 10
    
    def get_quiz_questions(self):
        """Retourne les questions du quiz pour ce module"""
        return self.quiz_questions.filter(is_active=True).order_by('order')

class QuizQuestion(models.Model):
    """Modèle pour les questions de quiz"""
    
    QUESTION_TYPES = [
        ('SINGLE', 'Choix unique'),
        ('MULTIPLE', 'Choix multiples'),
    ]
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='quiz_questions',
        verbose_name="Module"
    )
    
    order = models.PositiveIntegerField(
        verbose_name="Ordre",
        help_text="Ordre d'affichage de la question"
    )
    
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default='SINGLE',
        verbose_name="Type de question"
    )
    
    question_text = models.TextField(
        verbose_name="Texte de la question"
    )
    
    explanation = models.TextField(
        blank=True,
        verbose_name="Explication",
        help_text="Explication de la réponse correcte"
    )
    
    points = models.PositiveIntegerField(
        default=1,
        verbose_name="Points",
        help_text="Points attribués pour cette question"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Question active"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
        verbose_name = "Question de quiz"
        verbose_name_plural = "Questions de quiz"
    
    def __str__(self):
        return f"Q{self.order} - Module {self.module.number}: {self.question_text[:50]}..."
    
    def get_correct_answers(self):
        """Retourne les choix de réponse corrects"""
        return self.answer_choices.filter(is_correct=True)
    
    def get_total_points(self):
        """Retourne le total de points pour cette question"""
        return self.points

class AnswerChoice(models.Model):
    """Modèle pour les choix de réponse"""
    
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='answer_choices',
        verbose_name="Question"
    )
    
    choice_text = models.CharField(
        max_length=500,
        verbose_name="Texte du choix"
    )
    
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Réponse correcte"
    )
    
    order = models.PositiveIntegerField(
        verbose_name="Ordre d'affichage"
    )
    
    class Meta:
        ordering = ['question', 'order']
        unique_together = ['question', 'order']
        verbose_name = "Choix de réponse"
        verbose_name_plural = "Choix de réponses"
    
    def __str__(self):
        correct_indicator = " ✓" if self.is_correct else ""
        return f"{self.choice_text}{correct_indicator}"

class UserQuizAttempt(models.Model):
    """Modèle pour les tentatives de quiz des utilisateurs"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name="Utilisateur"
    )
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name="Module"
    )
    
    attempt_number = models.PositiveIntegerField(
        verbose_name="Numéro de tentative"
    )
    
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score (%)"
    )
    
    total_questions = models.PositiveIntegerField(
        verbose_name="Nombre total de questions"
    )
    
    correct_answers = models.PositiveIntegerField(
        verbose_name="Réponses correctes"
    )
    
    time_taken = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Temps pris (secondes)"
    )
    
    is_passed = models.BooleanField(
        default=False,
        verbose_name="Quiz réussi",
        help_text="Vrai si le score >= 80%"
    )
    
    started_at = models.DateTimeField(
        verbose_name="Début de la tentative"
    )
    
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fin de la tentative"
    )
    
    class Meta:
        ordering = ['-completed_at']
        unique_together = ['user', 'module', 'attempt_number']
        verbose_name = "Tentative de quiz"
        verbose_name_plural = "Tentatives de quiz"
    
    def __str__(self):
        return f"{self.user.full_name} - Module {self.module.number} - Tentative {self.attempt_number}"
    
    def save(self, *args, **kwargs):
        # Marquer comme réussi si score >= 80%
        self.is_passed = self.score >= 80.0
        super().save(*args, **kwargs)

class UserQuizAnswer(models.Model):
    """Modèle pour les réponses individuelles des utilisateurs"""
    
    attempt = models.ForeignKey(
        UserQuizAttempt,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name="Tentative"
    )
    
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        verbose_name="Question"
    )
    
    selected_choices = models.ManyToManyField(
        AnswerChoice,
        verbose_name="Choix sélectionnés"
    )
    
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Réponse correcte"
    )
    
    points_earned = models.FloatField(
        default=0,
        verbose_name="Points obtenus"
    )
    
    answered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Répondu le"
    )
    
    class Meta:
        unique_together = ['attempt', 'question']
        verbose_name = "Réponse utilisateur"
        verbose_name_plural = "Réponses utilisateur"
    
    def __str__(self):
        return f"{self.attempt.user.full_name} - Q{self.question.order}"