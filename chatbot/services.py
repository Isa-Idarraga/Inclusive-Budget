# chatbot/services.py
from projects.models import Project, EntradaMaterial, Worker
from catalog.models import Material

def get_context_data():
    proyectos = list(Project.objects.values("id", "name", "presupuesto", "presupuesto_gastado"))
    materiales = list(
        Material.objects.values(
            "id", "sku", "name", "category", "stock", "unit__symbol", "unit_cost"
        )
    )

    trabajadores = list(Worker.objects.values("id", "name", "role",))

    return {
        "proyectos": proyectos,
        "materiales": materiales,
        "trabajadores": trabajadores,
    }
