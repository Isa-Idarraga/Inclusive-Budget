import os
import sys
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from projects.models import Project, EntradaMaterial, ConsumoMaterial, ProyectoMaterial
from catalog.models import Material
from django.db.models import Sum, F, ExpressionWrapper

print('=== INSPECCIÓN RÁPIDA DE DATOS (solo lectura) ===')
print()

# Count globals
print('Total Projects:', Project.objects.count())
print('Total EntradaMaterial:', EntradaMaterial.objects.count())
print('Total ConsumoMaterial:', ConsumoMaterial.objects.count())
print('Total ProyectoMaterial:', ProyectoMaterial.objects.count())
print('Total Materials:', Material.objects.count())
print()

print('--- Proyectos: presupuesto vs campo presupuesto_gastado y calculado ---')
for p in Project.objects.all():
    # presupuesto_gastado field and computed
    try:
        calc = p.presupuesto_gastado_calculado
    except Exception as e:
        calc = f'ERROR: {e}'
    print(f'Project {p.id} | {p.name} | presupuesto={p.presupuesto} | presupuesto_gastado_field={p.presupuesto_gastado} | presupuesto_gastado_calculado={calc}')

print()
print('--- Entradas por proyecto (sumas y última entrada) ---')
ents = EntradaMaterial.objects.values('proyecto').annotate(total_cantidad=Sum('cantidad'), total_cost=Sum(ExpressionWrapper(F('cantidad') * F('material__unit_cost'), output_field=F('cantidad').output_field.__class__)))
for e in ents:
    print('Proyecto id', e['proyecto'], 'total_cantidad=', e['total_cantidad'], 'total_cost=', e['total_cost'])

print()
print('--- Consumos por proyecto (sumas de cantidad) ---')
cons = ConsumoMaterial.objects.values('proyecto').annotate(total_consumido=Sum('cantidad_consumida'))
for c in cons:
    print('Proyecto id', c['proyecto'], 'total_consumido=', c['total_consumido'])

print()
print('--- Materiales con stock y presentation_qty (primeros 30) ---')
for m in Material.objects.all()[:30]:
    print(f'Material {m.id} {m.sku} {m.name} stock={m.stock} presentation_qty={m.presentation_qty} unit_cost={getattr(m, "unit_cost", "N/A")}')

print('\n--- ProyectoMaterial (stock por proyecto) sample (primeros 30) ---')
for pm in ProyectoMaterial.objects.select_related('proyecto','material')[:30]:
    print(f'PM proyecto={pm.proyecto.id}:{pm.proyecto.name} material={pm.material.id}:{pm.material.name} stock_proyecto={pm.stock_proyecto}')

print('\n--- FIN DE LA INSPECCIÓN ---')
