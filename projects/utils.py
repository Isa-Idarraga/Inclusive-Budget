# projects/utils.py

def get_etapas_con_avance(proyecto):
    """
    Devuelve una lista de etapas del presupuesto con sus valores de:
    - presupuesto asignado
    - gasto ejecutado (sumatoria de consumos)
    - porcentaje ejecutado
    - estado visual (Pendiente, Bajo presupuesto, En el límite, Sobrecosto)
    """

    # Traer las etapas (budget_sections) con sus consumos relacionados
    etapas = proyecto.budget_sections.all().prefetch_related("consumos_materiales", "items")

    resultado = []

    for etapa in etapas:
        presupuesto = etapa.total_presupuesto or 0
        gasto = 0

        # Sumar todos los consumos relacionados con la etapa
        for c in etapa.consumos_materiales.all():
            gasto += (c.cantidad_consumida or 0) * (c.material.unit_cost or 0)

        porcentaje = (gasto / presupuesto) * 100 if presupuesto > 0 else 0

        # Determinar estado visual
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
