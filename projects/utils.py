from django.db.models import Sum, F

def create_default_budget_sections(project):
    """
    Función segura que NO crea secciones nuevas.
    Solo verifica que existan las secciones base predefinidas (plantillas)
    utilizadas en el formulario de presupuesto detallado.
    """

    from .models import BudgetSection

    # Verificar si existen las plantillas globales
    base_sections = BudgetSection.objects.filter(project__isnull=True).order_by("order")

    if base_sections.exists():
        print(f"ℹ️ Se detectaron {base_sections.count()} secciones base globales. "
              f"No se crearán nuevas secciones para el proyecto '{project.name}'.")
        return

    # Si no existen plantillas, solo avisar (no crear nada)
    print(f"⚠️ No se encontraron secciones base globales. "
          f"Verifica que las plantillas del formulario estén registradas correctamente.")


def get_etapas_con_avance(proyecto):
    """
    Devuelve la lista de las 23 secciones base del presupuesto (plantillas globales)
    con los valores del proyecto:
    - presupuesto planificado
    - gasto ejecutado (ConsumoMaterial)
    - porcentaje ejecutado
    - estado visual
    """
    from django.db.models import Sum, F
    from .models import BudgetSection, ProjectBudgetItem, ConsumoMaterial

    # Usar las secciones globales (plantillas)
    etapas = BudgetSection.objects.filter(project__isnull=True).order_by("order")

    resultado = []

    for etapa in etapas:
        # 🔹 Presupuesto planificado: suma de los ítems del proyecto en esa etapa
        presupuesto = (
            ProjectBudgetItem.objects.filter(
                project=proyecto, budget_item__section=etapa
            ).aggregate(total=Sum(F("quantity") * F("unit_price")))["total"]
            or 0
        )

        # 🔹 Gasto ejecutado: suma de consumos asociados a esa sección
        gasto = (
            ConsumoMaterial.objects.filter(
                proyecto=proyecto, etapa_presupuesto=etapa
            ).aggregate(total=Sum(F("cantidad_consumida") * F("material__unit_cost")))["total"]
            or 0
        )

        porcentaje = (gasto / presupuesto * 100) if presupuesto > 0 else 0

        if gasto == 0:
            estado = "Pendiente de inicio"
        elif porcentaje < 80:
            estado = "Bajo presupuesto"
        elif 80 <= porcentaje <= 100:
            estado = "En el límite"
        else:
            estado = "Sobrecosto"

        resultado.append({
            "id": etapa.id,
            "nombre": etapa.name,
            "presupuesto": presupuesto,
            "gasto": gasto,
            "porcentaje": porcentaje,
            "estado": estado,
        })

    return resultado
