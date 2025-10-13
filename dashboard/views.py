# dashboard/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from users.models import User
from django.conf import settings
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q
from projects.models import Project
from catalog.models import Material
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from decimal import Decimal
from .kpis import compute_kpis_from_django


@login_required
def home_router(request):
    u = request.user
    if u.is_superuser:  # si quieres que el superuser vea algo especial, decide aquí
        return redirect("dashboard:kpis")  # redirigir al dashboard con KPIs

    # Nuevos roles
    if u.role == User.JEFE:
        return redirect("dashboard:kpis")
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
@require_GET
def kpis(request):
    """Devuelve los KPIs básicos que se muestran en el dashboard del Jefe.

    KPIs calculados:
    - porcentaje_avance: porcentaje medio del presupuesto gastado sobre presupuesto entre proyectos activos
    - materiales_bajo_stock: lista de materiales cuyo stock global <= umbral (query param o 10 por defecto)
    - proyectos_desviacion: proyectos donde la desviación (gastado/presupuesto) supera el umbral (default 10%)
    - resumen_financiero: sumas consolidadas de presupuesto y gastado
    """
    # Umbrales configurables via query params
    try:
        material_threshold = float(request.GET.get("material_threshold", 10))
    except ValueError:
        material_threshold = 10.0

    try:
        desviacion_threshold = float(request.GET.get("desviacion_threshold", 10))
    except ValueError:
        desviacion_threshold = 10.0

    proyectos = Project.objects.filter(~Q(estado="futuro"))

    # Resumen financiero consolidado
    resumen = proyectos.aggregate(
        total_presupuesto=Sum("presupuesto"),
        total_gastado=Sum("presupuesto_gastado"),
    )

    total_presupuesto = resumen.get("total_presupuesto") or 0
    total_gastado = resumen.get("total_gastado") or 0

    saldo = total_presupuesto - total_gastado

    porcentaje_avance = 0
    if total_presupuesto and total_presupuesto > 0:
        porcentaje_avance = (total_gastado / total_presupuesto) * 100

    # Materiales con stock bajo (porcentaje de presentation_qty)
    materiales_bajo = Material.objects.filter(stock__lte=F('presentation_qty') * (material_threshold/100.0))

    # Proyectos con desviación significativa
    proyectos_desviacion = []
    for p in proyectos:
        if p.presupuesto and p.presupuesto > 0:
            porcentaje = (p.presupuesto_gastado / p.presupuesto) * 100
            if abs(porcentaje - 100) >= desviacion_threshold:
                proyectos_desviacion.append({
                    "id": p.id,
                    "name": p.name,
                    "presupuesto": p.presupuesto,
                    "gastado": p.presupuesto_gastado,
                    "porcentaje": porcentaje,
                })

    context = {
        "porcentaje_avance": round(porcentaje_avance, 2),
        "materiales_bajo_stock": materiales_bajo[:20],
        "proyectos_desviacion": proyectos_desviacion,
        "resumen_financiero": {
            "total_presupuesto": total_presupuesto,
            "total_gastado": total_gastado,
            "saldo": saldo,
        },
        "desviacion_threshold": desviacion_threshold,
        "material_threshold": material_threshold,
    }

    return render(request, "dashboard/home_jefe.html", context)


@login_required
@require_GET
def kpis_data(request):
    """Endpoint JSON que devuelve los KPIs para consumo por frontend (Chart.js).

    Devuelve:
    - porcentaje_avance
    - resumen_financiero (total_presupuesto, total_gastado)
    - materiales: lista de {id, sku, name, stock, unit}
    - proyectos: lista de {id, name, presupuesto, gastado, porcentaje}
    """
    try:
        material_threshold = float(request.GET.get("material_threshold", 10))
    except ValueError:
        material_threshold = 10.0

    try:
        desviacion_threshold = float(request.GET.get("desviacion_threshold", 10))
    except ValueError:
        desviacion_threshold = 10.0

    proyectos_qs = Project.objects.filter(~Q(estado="futuro"))
    materiales_qs = Material.objects.filter(stock__lte=F('presentation_qty') * (material_threshold/100.0))

    payload = compute_kpis_from_django(proyectos_qs, materiales_qs, material_threshold=material_threshold, desviacion_threshold=desviacion_threshold)

    # round floats for JSON safety where applicable
    payload['porcentaje_avance'] = round(float(payload.get('porcentaje_avance', 0)), 2)
    payload['resumen_financiero']['total_presupuesto'] = float(payload['resumen_financiero']['total_presupuesto'])
    payload['resumen_financiero']['total_gastado'] = float(payload['resumen_financiero']['total_gastado'])

    return JsonResponse(payload)


@login_required
def home_constructor(request):
    """Vista de inicio para el CONSTRUCTOR - Gestión de proyectos y materiales"""
    return render(request, "dashboard/home_constructor.html")


@login_required
def home_comercial(request):
    """Vista de inicio para el COMERCIAL - Solo crear presupuestos"""
    return render(request, "dashboard/home_comercial.html")
