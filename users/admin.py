# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

# Detecta si el modelo ya tiene el campo "role"
try:
    User._meta.get_field("role")
    HAS_ROLE = True
except Exception:
    HAS_ROLE = False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # fieldsets y add_fieldsets (solo agregamos "role" si existe)
    if HAS_ROLE:
        fieldsets = DjangoUserAdmin.fieldsets + ((_("Rol"), {"fields": ("role",)}),)
        add_fieldsets = DjangoUserAdmin.add_fieldsets + ((None, {"fields": ("role",)}),)

    # list_display / list_filter sin romper si no hay role aún
    base_list_display = ("username", "email", "first_name", "last_name", "is_staff")
    list_display = base_list_display + (("role",) if HAS_ROLE else ())

    base_list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    list_filter = base_list_filter + (("role",) if HAS_ROLE else ())

    search_fields = ("username", "first_name", "last_name", "email")
