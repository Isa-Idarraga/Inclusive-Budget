# chatbot/services/context_service.py
from projects.models import Project, Worker
from catalog.models import Material


def get_context_data():
    """
    Obtiene datos del contexto del sistema para el LLM
    
    Returns:
        dict: Diccionario con proyectos, materiales y trabajadores
    """
    try:
        proyectos = list(Project.objects.values(
            "id", "name", "presupuesto", "presupuesto_gastado"
        ))
        
        materiales = list(Material.objects.values(
            "id", "sku", "name", "category", "stock", "unit__symbol", "unit_cost"
        ))
        
        trabajadores = list(Worker.objects.values(
            "id", "name", "role"
        ))
        
        return {
            "proyectos": proyectos,
            "materiales": materiales,
            "trabajadores": trabajadores,
        }
    except Exception as e:
        print(f"⚠️ Error cargando contexto: {e}")
        return {
            "proyectos": [],
            "materiales": [],
            "trabajadores": []
        }