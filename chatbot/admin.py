# chatbot/admin.py
from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'state', 'flow_type', 'progress', 'created_at', 'updated_at']
    list_filter = ['state', 'flow_type', 'created_at']
    search_fields = ['title', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'title', 'state', 'flow_type')
        }),
        ('Progreso', {
            'fields': ('current_step', 'total_steps')
        }),
        ('Datos Recolectados', {
            'fields': ('collected_data',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress(self, obj):
        if obj.total_steps > 0:
            percentage = (obj.current_step / obj.total_steps) * 100
            return f"{obj.current_step}/{obj.total_steps} ({percentage:.0f}%)"
        return "0/0"
    progress.short_description = "Progreso"
    
    def has_add_permission(self, request):
        # No permitir crear conversaciones manualmente desde el admin
        return False


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información', {
            'fields': ('conversation', 'role', 'content')
        }),
        ('Metadatos', {
            'fields': ('meta',),
            'classes': ('collapse',)
        }),
        ('Fecha', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = "Contenido"
    
    def has_add_permission(self, request):
        # No permitir crear mensajes manualmente desde el admin
        return False