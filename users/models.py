# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    JEFE_OBRA = "JEFE_OBRA"
    GESTOR_INVENTARIO = "GESTOR_INVENTARIO"
    ROLE_CHOICES = [
        (JEFE_OBRA, "Jefe de obra"),
        (GESTOR_INVENTARIO, "Gestor de inventario"),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=JEFE_OBRA)

    def can_see(self, module: str) -> bool:
        if self.is_superuser:
            return True
        visible = {
            self.JEFE_OBRA: {"projects", "dashboard"},
            self.GESTOR_INVENTARIO: {"catalog", "dashboard"},
        }
        return module in visible.get(self.role, set())
