# dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from users.models import User


@login_required
def home_router(request):
    u = request.user
    if u.is_superuser:  # si quieres que el superuser vea algo especial, decide aquí
        return redirect("dashboard:home_jefe")  # o a "admin:index" si prefieres el admin

    # Nuevos roles
    if u.role == User.JEFE:
        return redirect("dashboard:home_jefe")
    if u.role == User.CONSTRUCTOR:
        return redirect("dashboard:home_constructor")
    if u.role == User.COMERCIAL:
        return redirect("dashboard:home_comercial")

    # fallback por si el usuario no tiene rol (o algo raro)
    return redirect("login")


@login_required
def home_jefe(request):
    """Vista de inicio para el JEFE - Acceso total"""
    return render(request, "dashboard/home_jefe.html")


@login_required
def home_constructor(request):
    """Vista de inicio para el CONSTRUCTOR - Gestión de proyectos y materiales"""
    return render(request, "dashboard/home_constructor.html")


@login_required
def home_comercial(request):
    """Vista de inicio para el COMERCIAL - Solo crear presupuestos"""
    return render(request, "dashboard/home_comercial.html")
