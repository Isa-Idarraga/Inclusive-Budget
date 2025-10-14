# chatbot/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class ConversationState(models.TextChoices):
    """Estados posibles de una conversación"""
    IDLE = "idle", "Inactiva"
    MANUAL_FLOW = "manual_flow", "Flujo Manual"
    AI_FLOW = "ai_flow", "Flujo IA"
    COMPLETED = "completed", "Completada"


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200, blank=True)
    state = models.CharField(
        max_length=50,
        choices=ConversationState.choices,
        default=ConversationState.IDLE
    )
    flow_type = models.CharField(
        max_length=20,
        choices=[("manual", "Manual"), ("ai", "IA")],
        null=True,
        blank=True
    )
    
    # Progreso del flujo
    current_step = models.IntegerField(default=0)
    total_steps = models.IntegerField(default=0)
    
    # Datos recolectados
    collected_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or f"Conversación #{self.id}"

    def is_active(self):
        return self.state in [ConversationState.MANUAL_FLOW, ConversationState.AI_FLOW]

    def mark_completed(self):
        self.state = ConversationState.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def reset(self):
        self.state = ConversationState.IDLE
        self.current_step = 0
        self.collected_data = {}
        self.flow_type = None
        self.save()


class Message(models.Model):
    ROLE_CHOICES = [
        ("system", "Sistema"),
        ("user", "Usuario"),
        ("assistant", "Asistente"),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    meta = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}..."