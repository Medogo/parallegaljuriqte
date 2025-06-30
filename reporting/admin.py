# reporting/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import CommunityReport, ReportAttachment, AudioReport, ReportFollowUp

class ReportAttachmentInline(admin.TabularInline):
    """Inline pour les pièces jointes"""
    model = ReportAttachment
    extra = 0
    readonly_fields = ['filename', 'file_size', 'uploaded_at']
    fields = ['file', 'filename', 'file_size', 'description']

class ReportFollowUpInline(admin.TabularInline):
    """Inline pour les suivis de signalement"""
    model = ReportFollowUp
    extra = 1
    fields = ['update_type', 'message', 'author', 'is_public']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')

@admin.register(CommunityReport)
class CommunityReportAdmin(admin.ModelAdmin):
    """Administration des signalements communautaires"""
    
    list_display = [
        'report_id_short', 'title', 'problem_type', 'reporter_name', 
        'commune', 'status', 'priority_level', 'created_at'
    ]
    list_filter = [
        'problem_type', 'status', 'priority_level', 'is_anonymous', 
        'commune', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'location', 'user__full_name', 
        'user__phone_number', 'commune'
    ]
    ordering = ['-created_at']
    
    readonly_fields = [
        'report_id', 'user', 'created_at', 'updated_at', 'reporter_info_display'
    ]
    
    fieldsets = (
        ('Signalement', {
            'fields': (
                'report_id', 'user', 'reporter_info_display', 'problem_type', 
                'title', 'description'
            )
        }),
        ('Incident', {
            'fields': ('location', 'commune', 'incident_date', 'incident_time')
        }),
        ('Options', {
            'fields': ('is_anonymous', 'contact_allowed')
        }),
        ('Gestion', {
            'fields': (
                'status', 'priority_level', 'assigned_to', 'admin_notes', 
                'resolution_notes', 'resolved_at'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ReportAttachmentInline, ReportFollowUpInline]
    
    def report_id_short(self, obj):
        """Affiche une version courte de l'ID"""
        return obj.report_id.hex[:8]
    report_id_short.short_description = "ID"
    
    def reporter_name(self, obj):
        """Affiche le nom du rapporteur avec indication d'anonymat"""
        if obj.is_anonymous:
            return format_html('<em>Anonyme</em>')
        return obj.user.full_name
    reporter_name.short_description = "Rapporteur"
    
    def reporter_info_display(self, obj):
        """Affiche les informations complètes du rapporteur"""
        info = obj.reporter_info
        contact_status = "Autorisé" if obj.can_be_contacted() else "Non autorisé"
        
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Téléphone:</strong> {}<br>'
            '<strong>Commune:</strong> {}<br>'
            '<strong>Contact:</strong> {}',
            info['name'], info['phone'], info['commune'], contact_status
        )
    reporter_info_display.short_description = "Informations rapporteur"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Actions personnalisées
    def mark_under_review(self, request, queryset):
        """Marquer comme en cours d'examen"""
        count = queryset.update(status='UNDER_REVIEW')
        self.message_user(request, f"{count} signalement(s) marqué(s) en cours d'examen.")
    mark_under_review.short_description = "Marquer en cours d'examen"
    
    def mark_resolved(self, request, queryset):
        """Marquer comme résolu"""
        count = queryset.update(status='RESOLVED', resolved_at=timezone.now())
        self.message_user(request, f"{count} signalement(s) marqué(s) comme résolu(s).")
    mark_resolved.short_description = "Marquer comme résolu"
    
    def set_high_priority(self, request, queryset):
        """Définir priorité élevée"""
        count = queryset.update(priority_level='HIGH')
        self.message_user(request, f"{count} signalement(s) défini(s) en priorité élevée.")
    set_high_priority.short_description = "Priorité élevée"
    
    actions = ['mark_under_review', 'mark_resolved', 'set_high_priority']

@admin.register(AudioReport)
class AudioReportAdmin(admin.ModelAdmin):
    """Administration des signalements audio"""
    
    list_display = [
        'report_id_short', 'reporter_name', 'duration_formatted', 
        'status', 'consent_given', 'transcribed_status', 'created_at'
    ]
    list_filter = [
        'status', 'consent_given', 'is_anonymous', 'created_at',
        'transcribed_at'
    ]
    search_fields = [
        'transcription', 'extracted_location', 'user__full_name',
        'user__phone_number'
    ]
    ordering = ['-created_at']
    
    readonly_fields = [
        'report_id', 'user', 'file_size', 'created_at', 'updated_at',
        'reporter_info_display', 'audio_player'
    ]
    
    fieldsets = (
        ('Signalement Audio', {
            'fields': (
                'report_id', 'user', 'reporter_info_display', 'audio_file',
                'audio_player', 'duration', 'file_size'
            )
        }),
        ('Consentement', {
            'fields': ('consent_given', 'is_anonymous')
        }),
        ('Transcription', {
            'fields': (
                'transcription', 'transcribed_by', 'transcribed_at',
                'extracted_problem_type', 'extracted_location'
            )
        }),
        ('Gestion', {
            'fields': ('status', 'assigned_to', 'admin_notes')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ReportFollowUpInline]
    
    def report_id_short(self, obj):
        """Affiche une version courte de l'ID"""
        return obj.report_id.hex[:8]
    report_id_short.short_description = "ID"
    
    def reporter_name(self, obj):
        """Affiche le nom du rapporteur avec indication d'anonymat"""
        if obj.is_anonymous:
            return format_html('<em>Anonyme</em>')
        return obj.user.full_name
    reporter_name.short_description = "Rapporteur"
    
    def transcribed_status(self, obj):
        """Indique le statut de transcription"""
        if obj.transcription:
            return format_html('<span style="color: green;">✓ Transcrit</span>')
        return format_html('<span style="color: orange;">En attente</span>')
    transcribed_status.short_description = "Transcription"
    
    def reporter_info_display(self, obj):
        """Affiche les informations complètes du rapporteur"""
        info = obj.reporter_info
        return format_html(
            '<strong>Nom:</strong> {}<br>'
            '<strong>Téléphone:</strong> {}<br>'
            '<strong>Commune:</strong> {}',
            info['name'], info['phone'], info['commune']
        )
    reporter_info_display.short_description = "Informations rapporteur"
    
    def audio_player(self, obj):
        """Affiche un lecteur audio HTML5"""
        if obj.audio_file:
            return format_html(
                '<audio controls style="width: 300px;">'
                '<source src="{}" type="audio/mpeg">'
                'Votre navigateur ne supporte pas l\'élément audio.'
                '</audio>',
                obj.audio_file.url
            )
        return "Aucun fichier audio"
    audio_player.short_description = "Lecteur audio"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Actions personnalisées
    def mark_transcribed(self, request, queryset):
        """Marquer comme transcrit"""
        count = queryset.update(
            status='TRANSCRIBED', 
            transcribed_at=timezone.now(),
            transcribed_by=request.user.get_full_name() or request.user.username
        )
        self.message_user(request, f"{count} signalement(s) audio marqué(s) comme transcrit(s).")
    mark_transcribed.short_description = "Marquer comme transcrit"
    
    def mark_under_review(self, request, queryset):
        """Marquer comme en cours d'examen"""
        count = queryset.update(status='UNDER_REVIEW')
        self.message_user(request, f"{count} signalement(s) audio marqué(s) en cours d'examen.")
    mark_under_review.short_description = "Marquer en cours d'examen"
    
    actions = ['mark_transcribed', 'mark_under_review']

@admin.register(ReportFollowUp)
class ReportFollowUpAdmin(admin.ModelAdmin):
    """Administration des suivis de signalements"""
    
    list_display = [
        'get_report_info', 'update_type', 'author', 'is_public', 'created_at'
    ]
    list_filter = ['update_type', 'is_public', 'created_at']
    search_fields = ['message', 'author']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Signalement', {
            'fields': ('text_report', 'audio_report')
        }),
        ('Suivi', {
            'fields': ('update_type', 'message', 'author', 'is_public')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_report_info(self, obj):
        """Affiche les informations du signalement associé"""
        if obj.text_report:
            return format_html(
                'Textuel: {} ({})',
                obj.text_report.title,
                obj.text_report.report_id.hex[:8]
            )
        elif obj.audio_report:
            return format_html(
                'Audio: {} ({})',
                obj.audio_report.reporter_info['name'],
                obj.audio_report.report_id.hex[:8]
            )
        return "N/A"
    get_report_info.short_description = "Signalement"
    
    def clean(self):
        """Validation personnalisée"""
        super().clean()
        if not self.text_report and not self.audio_report:
            raise admin.ValidationError(
                "Un suivi doit être associé à un signalement (textuel ou audio)."
            )
        if self.text_report and self.audio_report:
            raise admin.ValidationError(
                "Un suivi ne peut être associé qu'à un seul type de signalement."
            )

# Configuration de l'admin site
admin.site.site_header = "Administration Paralegal App"
admin.site.site_title = "Paralegal Admin"
admin.site.index_title = "Gestion de l'application de formation parajuridique"

# Ajout de statistiques dans l'index admin
class AdminStatsView:
    """Vue pour afficher des statistiques dans l'admin"""
    
    @staticmethod
    def get_stats():
        from accounts.models import CustomUser
        from modules.models import Module
        
        stats = {
            'total_users': CustomUser.objects.count(),
            'french_users': CustomUser.objects.filter(preferred_language='FR').count(),
            'fon_users': CustomUser.objects.filter(preferred_language='FON').count(),
            'total_modules': Module.objects.filter(is_active=True).count(),
            'total_text_reports': CommunityReport.objects.count(),
            'total_audio_reports': AudioReport.objects.count(),
            'pending_reports': (
                CommunityReport.objects.filter(status='PENDING').count() +
                AudioReport.objects.filter(status='PENDING').count()
            )
        }
        return stats