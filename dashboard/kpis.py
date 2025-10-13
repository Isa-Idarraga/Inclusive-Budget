"""Helper functions to compute dashboard KPI aggregates.

This module exposes two functions:
- compute_kpis: pure-Python function that works on plain iterables of dict-like objects
- compute_kpis_from_django: convenience wrapper that accepts Django QuerySets for projects and materials

Keeping numeric logic here makes it easy to unit-test without DB and to reuse in views.
"""
from typing import Iterable, Dict, Any


def compute_kpis(projects: Iterable[Dict[str, Any]], materials: Iterable[Dict[str, Any]],
                 material_threshold: float = 10.0, desviacion_threshold: float = 10.0) -> Dict[str, Any]:
    """Compute KPI-like aggregates from simple lists of dict-like objects.

    projects: iterable of dicts with keys: presupuesto, presupuesto_gastado, id, name
    materials: iterable of dicts with keys: stock, presentation_qty
    Returns dict with porcentaje_avance, resumen_financiero, materiales (filtered), proyectos (deviations)
    """
    total_presupuesto = 0.0
    total_gastado = 0.0

    proyectos_list = list(projects)
    for p in proyectos_list:
        presupuesto = p.get('presupuesto') or 0.0
        gastado = p.get('presupuesto_gastado') or 0.0
        # Ensure numeric types are floats for aggregation
        presupuesto_f = float(presupuesto)
        gastado_f = float(gastado)
        total_presupuesto += presupuesto_f
        total_gastado += gastado_f

    porcentaje_avance = 0.0
    if total_presupuesto and total_presupuesto > 0:
        porcentaje_avance = (total_gastado / total_presupuesto) * 100

    # materiales bajo stock: stock <= presentation_qty * (threshold/100)
    materiales_bajo = []
    for m in materials:
        stock = float(m.get('stock', 0))
        pres = float(m.get('presentation_qty', 0))
        if stock <= pres * (material_threshold / 100.0):
            materiales_bajo.append(m)

    proyectos_desviacion = []
    for p in proyectos_list:
        presupuesto = p.get('presupuesto') or 0.0
        gastado = p.get('presupuesto_gastado') or 0.0
        porcentaje = None
        # Work with floats to avoid mixing Decimal and float
        presupuesto_f = float(presupuesto)
        gastado_f = float(gastado)
        if presupuesto_f and presupuesto_f > 0:
            porcentaje = (gastado_f / presupuesto_f) * 100
            if abs(porcentaje - 100) >= desviacion_threshold:
                proyectos_desviacion.append({
                    'id': p.get('id'),
                    'name': p.get('name'),
                    'presupuesto': presupuesto_f,
                    'gastado': gastado_f,
                    'porcentaje': porcentaje,
                })

    return {
        'porcentaje_avance': round(porcentaje_avance, 2),
        'resumen_financiero': {
            'total_presupuesto': float(total_presupuesto),
            'total_gastado': float(total_gastado),
        },
        'materiales': materiales_bajo,
        'proyectos': proyectos_desviacion,
    }


def compute_kpis_from_django(projects_qs, materials_qs, material_threshold: float = 10.0, desviacion_threshold: float = 10.0):
    """Compute KPIs when given Django QuerySets for projects and materials.

    Returns the same shaped dict as compute_kpis.
    """
    # Build plain structures for reuse of compute_kpis logic
    proyectos = []
    for p in projects_qs:
        proyectos.append({
            'id': getattr(p, 'id', None),
            'name': getattr(p, 'name', ''),
            'presupuesto': getattr(p, 'presupuesto', 0),
            'presupuesto_gastado': getattr(p, 'presupuesto_gastado', 0),
        })

    materiales = []
    for m in materials_qs:
        materiales.append({
            'id': getattr(m, 'id', None),
            'sku': getattr(m, 'sku', ''),
            'name': getattr(m, 'name', ''),
            'stock': getattr(m, 'stock', 0),
            'presentation_qty': getattr(m, 'presentation_qty', 0),
            'unit': getattr(getattr(m, 'unit', None), 'symbol', '') if getattr(m, 'unit', None) else '',
        })

    return compute_kpis(proyectos, materiales, material_threshold=material_threshold, desviacion_threshold=desviacion_threshold)
