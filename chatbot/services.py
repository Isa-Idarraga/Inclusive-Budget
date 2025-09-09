# chatbot/services.py
from projects.models import Project, EntradaMaterial, Worker

def get_context_data():
    proyectos = list(Project.objects.values("id", "name", "presupuesto", "presupuesto_gastado"))
    materiales = list(EntradaMaterial.objects.values("id", "material__name", "cantidad"))
    trabajadores = list(Worker.objects.values("id", "name", "role",))

    return {
        "proyectos": proyectos,
        "materiales": materiales,
        "trabajadores": trabajadores,
    }
