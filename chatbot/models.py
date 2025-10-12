# chatbot/models.py
from django.conf import settings
from django.db import models

class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True, blank=True
    )
    title = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=50, default="idle")  # 👈 estado del flujo
    context = models.JSONField(default=dict, blank=True)     # 👈 datos temporales
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Conversación #{self.id}"


class Message(models.Model):
    ROLE_CHOICES = [
        ("system", "system"),
        ("user", "user"),
        ("assistant", "assistant"),
    ]
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    meta = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}..."
