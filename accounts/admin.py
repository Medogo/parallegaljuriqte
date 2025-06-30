# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Administration personnalisée pour le modèle CustomUser"""
    
    list_display = [
        'phone_number', 'full_name', 'commune', 'gender', 
        'preferred_language', 'is_profile_complete', 'registration_date'
    ]
    
    list_filter = [
        'gender', 'education_level', 'preferred_language', 
        'is_profile_complete', 'registration_date', 'commune'
    ]
    
    search_fields = ['phone_number', 'full_name', 'commune']
    
    ordering = ['-registration_date']
    
    readonly_fields = ['registration_date', 'is_profile_complete', 'last_login', 'date_joined']
    
    # Configuration des champs dans le formulaire d'édition
    fieldsets = (
        (_('Informations personnelles'), {
            'fields': (
                'full_name', 'phone_number', 'commune', 
                'gender', 'birth_date', 'education_level'
            )
        }),
        (_('Préférences'), {
            'fields': ('preferred_language',)
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Informations système'), {
            'fields': ('registration_date', 'is_profile_complete', 'last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuration pour l'ajout d'un nouvel utilisateur
    add_fieldsets = (
        (_('Informations obligatoires'), {
            'classes': ('wide',),
            'fields': (
                'full_name', 'phone_number', 'commune', 
                'gender', 'birth_date', 'education_level', 
                'preferred_language', 'password1', 'password2'
            ),
        }),
        (_('Permissions'), {
            'classes': ('wide', 'collapse'),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    def get_queryset(self, request):
        """Optimise les requêtes de l'admin"""
        return super().get_queryset(request).select_related()
    
    def has_delete_permission(self, request, obj=None):
        """Restreint la suppression des utilisateurs"""
        # Seuls les superutilisateurs peuvent supprimer
        return request.user.is_superuser
    
    # Actions personnalisées
    def mark_profile_complete(self, request, queryset):
        """Marque les profils sélectionnés comme complets"""
        count = queryset.update(is_profile_complete=True)
        self.message_user(
            request,
            f"{count} profil(s) marqué(s) comme complet(s)."
        )
    mark_profile_complete.short_description = "Marquer les profils comme complets"
    
    def deactivate_users(self, request, queryset):
        """Désactive les utilisateurs sélectionnés"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{count} utilisateur(s) désactivé(s)."
        )
    deactivate_users.short_description = "Désactiver les utilisateurs"
    
    actions = ['mark_profile_complete', 'deactivate_users']