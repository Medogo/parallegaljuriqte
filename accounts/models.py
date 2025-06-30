# authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """Modèle utilisateur personnalisé pour les parajuristes"""
    
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    EDUCATION_LEVELS = [
        ('NONE', 'Aucune instruction'),
        ('PRIMARY', 'Primaire'),
        ('SECONDARY', 'Secondaire'),
        ('HIGHER', 'Supérieur'),
    ]
    
    LANGUAGE_CHOICES = [
        ('FR', 'Français'),
        ('FON', 'Fon'),
    ]
    
    # Champs obligatoires selon le cahier des charges
    full_name = models.CharField(
        max_length=100,
        verbose_name="Nom complet",
        help_text="Nom et prénom complets"
    )
    
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{8,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés."
    )
    phone_number = models.CharField(
        validators=[phone_validator],
        max_length=17,
        unique=True,
        verbose_name="Numéro de téléphone"
    )
    
    commune = models.CharField(
        max_length=100,
        verbose_name="Commune/Quartier",
        help_text="Commune ou quartier de résidence"
    )
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name="Sexe"
    )
    
    birth_date = models.DateField(
        verbose_name="Date de naissance"
    )
    
    education_level = models.CharField(
        max_length=10,
        choices=EDUCATION_LEVELS,
        verbose_name="Niveau d'instruction"
    )
    
    preferred_language = models.CharField(
        max_length=3,
        choices=LANGUAGE_CHOICES,
        default='FR',
        verbose_name="Langue préférée"
    )
    
    # Champs additionnels
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )
    
    is_profile_complete = models.BooleanField(
        default=False,
        verbose_name="Profil complet"
    )
    
    # Utiliser le numéro de téléphone comme identifiant
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'commune', 'gender', 'birth_date', 'education_level']
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        db_table = 'auth_user'
    
    def __str__(self):
        return f"{self.full_name} - {self.phone_number}"
    
    def save(self, *args, **kwargs):
        # Marquer le profil comme complet si tous les champs requis sont remplis
        if (self.full_name and self.phone_number and self.commune and 
            self.gender and self.birth_date and self.education_level):
            self.is_profile_complete = True
        
        # Générer un username unique basé sur le numéro de téléphone
        if not self.username:
            self.username = self.phone_number
            
        super().save(*args, **kwargs)
    
    @property
    def age(self):
        """Calcule l'âge de l'utilisateur"""
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    def can_generate_certificate(self):
        """Vérifie si l'utilisateur peut générer un certificat"""
        # Cette méthode sera implémentée après la création des modèles de progression
        return False