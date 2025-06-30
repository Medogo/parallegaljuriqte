# progress/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import ModuleProgress, Certificate, OverallProgress, UserActivity

@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    """Administration de la progression des modules"""
    
    list_display = [
        'user', 'module', 'progress_percentage', 'is_completed', 
        'listening_time_formatted', 'updated_at'
    ]
    list_filter = ['is_completed', 'module', 'user__preferred_language', 'updated_at']
    search_fields = ['user__full_name', 'user__phone_number', 'module__title']
    ordering = ['-updated_at']
    
    readonly_fields = [
        'started_at', 'updated_at', 'completed_at', 'is_quiz_based', 'is_audio_based'
    ]
    
    fieldsets = (
        ('Progression', {
            'fields': ('user', 'module', 'progress_percentage', 'is_completed')
        }),
        ('Audio (Fon)', {
            'fields': ('last_audio_position', 'total_listening_time', 'listening_sessions'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('started_at', 'updated_at', 'completed_at', 'is_quiz_based', 'is_audio_based'),
            'classes': ('collapse',)
        }),
    )
    
    def listening_time_formatted(self, obj):
        """Affiche le temps d'écoute formaté"""
        if obj.total_listening_time:
            hours, remainder = divmod(obj.total_listening_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m {seconds}s"
        return "0"
    listening_time_formatted.short_description = "Temps d'écoute"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'module')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Administration des certificats"""
    
    list_display = [
        'verification_code', 'full_name', 'user_phone', 'completion_date', 
        'total_modules_completed', 'average_score', 'is_valid'
    ]
    list_filter = ['is_valid', 'completion_date', 'signed_by']
    search_fields = ['verification_code', 'full_name', 'user__phone_number']
    ordering = ['-completion_date']
    
    readonly_fields = [
        'certificate_id', 'verification_code', 'completion_date', 'user_info_display'
    ]
    
    fieldsets = (
        ('Certificat', {
            'fields': ('certificate_id', 'verification_code', 'full_name', 'completion_date')
        }),
        ('Utilisateur', {
            'fields': ('user', 'user_info_display'),
            'classes': ('collapse',)
        }),
        ('Résultats', {
            'fields': ('total_modules_completed', 'average_score', 'certificate_file')
        }),
        ('Validation', {
            'fields': ('is_valid', 'signed_by', 'signature_date')
        }),
    )
    
    def user_phone(self, obj):
        """Affiche le téléphone de l'utilisateur"""
        return obj.user.phone_number
    user_phone.short_description = "Téléphone"
    
    def user_info_display(self, obj):
        """Affiche les informations complètes de l'utilisateur"""
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Téléphone:</strong> {}<br>'
            '<strong>Commune:</strong> {}<br>'
            '<strong>Langue:</strong> {}',
            obj.user.full_name,
            obj.user.phone_number,
            obj.user.commune,
            obj.user.get_preferred_language_display()
        )
    user_info_display.short_description = "Informations utilisateur"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Actions personnalisées
    def mark_as_signed(self, request, queryset):
        """Marquer les certificats comme signés"""
        count = queryset.update(
            signed_by=request.user.get_full_name() or request.user.username,
            signature_date=timezone.now()
        )
        self.message_user(request, f"{count} certificat(s) marqué(s) comme signé(s).")
    mark_as_signed.short_description = "Marquer comme signés"
    
    def invalidate_certificates(self, request, queryset):
        """Invalider les certificats sélectionnés"""
        count = queryset.update(is_valid=False)
        self.message_user(request, f"{count} certificat(s) invalidé(s).")
    invalidate_certificates.short_description = "Invalider les certificats"
    
    actions = ['mark_as_signed', 'invalidate_certificates']

@admin.register(OverallProgress)
class OverallProgressAdmin(admin.ModelAdmin):
    """Administration de la progression globale"""
    
    list_display = [
        'user', 'completion_percentage', 'completed_modules', 'total_modules',
        'can_get_certificate', 'certificate_requested', 'completed_at'
    ]
    list_filter = [
        'can_get_certificate', 'certificate_requested', 'user__preferred_language',
        'completed_at'
    ]
    search_fields = ['user__full_name', 'user__phone_number']
    ordering = ['-completion_percentage', '-updated_at']
    
    readonly_fields = [
        'total_modules', 'completed_modules', 'completion_percentage',
        'total_quiz_attempts', 'average_quiz_score', 'total_audio_time',
        'started_at', 'updated_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Progression', {
            'fields': (
                'total_modules', 'completed_modules', 'completion_percentage',
                'can_get_certificate', 'certificate_requested'
            )
        }),
        ('Statistiques français', {
            'fields': ('total_quiz_attempts', 'average_quiz_score'),
            'classes': ('collapse',)
        }),
        ('Statistiques Fon', {
            'fields': ('total_audio_time',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('started_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Actions personnalisées
    def update_progress(self, request, queryset):
        """Mettre à jour la progression"""
        count = 0
        for progress in queryset:
            progress.update_progress()
            count += 1
        self.message_user(request, f"Progression mise à jour pour {count} utilisateur(s).")
    update_progress.short_description = "Mettre à jour la progression"
    
    def mark_certificate_eligible(self, request, queryset):
        """Marquer comme éligible au certificat"""
        count = queryset.update(can_get_certificate=True)
        self.message_user(request, f"{count} utilisateur(s) marqué(s) comme éligible(s).")
    mark_certificate_eligible.short_description = "Marquer éligible au certificat"
    
    actions = ['update_progress', 'mark_certificate_eligible']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Administration des activités utilisateur"""
    
    list_display = [
        'user', 'activity_type', 'module', 'timestamp', 'session_info'
    ]
    list_filter = ['activity_type', 'timestamp', 'module']
    search_fields = ['user__full_name', 'user__phone_number']
    ordering = ['-timestamp']
    
    readonly_fields = ['user', 'activity_type', 'module', 'details', 'timestamp', 'session_id', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Activité', {
            'fields': ('user', 'activity_type', 'module', 'details', 'timestamp')
        }),
        ('Session', {
            'fields': ('session_id', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def session_info(self, obj):
        """Affiche des informations de session"""
        if obj.ip_address:
            return f"IP: {obj.ip_address}"
        return "N/A"
    session_info.short_description = "Session"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'module')
    
    def has_add_permission(self, request):
        return False  # Empêcher la création manuelle
    
    def has_change_permission(self, request, obj=None):
        return False  # Empêcher la modification

# Actions globales
@admin.action(description='Exporter les données sélectionnées (CSV)')
def export_as_csv(modeladmin, request, queryset):
    """Action pour exporter en CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{modeladmin.model._meta.verbose_name_plural}.csv"'
    
    writer = csv.writer(response)
    
    # En-têtes
    field_names = [field.name for field in modeladmin.model._meta.fields]
    writer.writerow(field_names)
    
    # Données
    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            if value is None:
                value = ''
            row.append(str(value))
        writer.writerow(row)
    
    return response

# Ajouter l'action d'export à tous les admins
ModuleProgressAdmin.actions = [export_as_csv]
CertificateAdmin.actions.append(export_as_csv)
OverallProgressAdmin.actions.append(export_as_csv)