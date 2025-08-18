# dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from users.models import User  


@login_required
def home_router(request):
    u = request.user
    if u.is_superuser:                 # si quieres que el superuser vea algo especial, decide aquí
        return redirect("home_jefe")   # o a "admin:index" si prefieres el admin

    if u.role == User.JEFE_OBRA:
        return redirect("home_jefe")
    if u.role == User.GESTOR_INVENTARIO:
        return redirect("home_gestor")

    # fallback por si el usuario no tiene rol (o algo raro)
    return redirect("login")


@login_required
def home_jefe(request):
    return render(request, "dashboard/home_jefe.html")


@login_required
def home_gestor(request):
    return render(request, "dashboard/home_gestor.html")