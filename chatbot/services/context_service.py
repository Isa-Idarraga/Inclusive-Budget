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
        # ✅ CORREGIR: usar 'fecha_creacion' en lugar de 'created_at'
        proyectos = list(Project.objects.all().values(
            "id", "name", "presupuesto", "presupuesto_gastado", "estado"
        ).order_by('-fecha_creacion')[:20])  # Últimos 20
        
        materiales = list(Material.objects.all().values(
            "id", "sku", "name", "category", "stock", "unit__symbol", "unit_cost"
        ).order_by('category', 'name')[:50])  # Máximo 50 materiales
        
        trabajadores = list(Worker.objects.all().values(
            "id", "name", "role"
        ).order_by('role', 'name')[:30])  # Máximo 30 trabajadores
        
        print(f"✅ Contexto cargado: {len(proyectos)} proyectos, {len(materiales)} materiales, {len(trabajadores)} trabajadores")
        
        return {
            "proyectos": proyectos,
            "materiales": materiales,
            "trabajadores": trabajadores,
        }
    except Exception as e:
        print(f"⚠️ Error cargando contexto: {e}")
        import traceback
        traceback.print_exc()
        return {
            "proyectos": [],
            "materiales": [],
            "trabajadores": []
        }