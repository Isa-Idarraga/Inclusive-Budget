# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    COMERCIAL = "COMERCIAL"
    CONSTRUCTOR = "CONSTRUCTOR"
    JEFE = "JEFE"

    ROLE_CHOICES = [
        (COMERCIAL, "Usuario Comercial"),
        (CONSTRUCTOR, "Usuario Constructor"),
        (JEFE, "Jefe"),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=COMERCIAL)

    def can_see(self, module: str) -> bool:
        """Define qué módulos puede ver cada rol"""
        if self.is_superuser or self.role == self.JEFE:
            return True

        visible = {
            self.COMERCIAL: {"projects_create"},  # Solo crear proyectos
            self.CONSTRUCTOR: {"projects", "catalog", "dashboard"},  # Ve todo pero con restricciones
        }
        return module in visible.get(self.role, set())

    def can_edit_project(self, project) -> bool:
        """Define si puede editar un proyecto específico"""
        if self.is_superuser or self.role == self.JEFE:
            return True
        if self.role == self.CONSTRUCTOR:
            # Solo puede editar sus propios proyectos
            return project.creado_por_id == self.id
        return False

    def can_access_project_board(self, project) -> bool:
        """Define si puede acceder al tablero de control (calendario interactivo)"""
        if self.is_superuser or self.role == self.JEFE:
            return True
        if self.role == self.CONSTRUCTOR:
            # Solo accede al board de sus propios proyectos
            return project.creado_por_id == self.id
        return False

    def can_manage_users(self) -> bool:
        """Solo el JEFE puede crear y gestionar usuarios"""
        return self.is_superuser or self.role == self.JEFE
