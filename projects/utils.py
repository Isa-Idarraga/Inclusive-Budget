# projects/utils.py

def get_etapas_con_avance(proyecto):
    """
    Devuelve una lista de etapas del presupuesto con sus valores de:
    - presupuesto asignado
    - gasto ejecutado (sumatoria de consumos)
    - porcentaje ejecutado
    - estado visual (Pendiente, Bajo presupuesto, En el límite, Sobrecosto)
    """

    # ✅ En tu modelo, las etapas se relacionan como 'budget_sections'
    etapas = proyecto.budget_sections.all().prefetch_related(
        "budget_items",
        "budget_items__consumos",
        "budget_items__consumos__material"
    )

    resultado = []

    for etapa in etapas:
        presupuesto = etapa.total_presupuesto or 0  # campo acumulado de la sección
        gasto = 0

        # 🔄 Sumar todos los consumos de los ítems de esta etapa
        for item in etapa.budget_items.all():
            consumos = getattr(item, "consumos", None)
            if consumos:
                for c in consumos.all():
                    gasto += (c.cantidad or 0) * (c.material.unit_cost or 0)

        # 📊 Calcular porcentaje
        porcentaje = (gasto / presupuesto) * 100 if presupuesto > 0 else 0

        # 🟢🟡🔴 Determinar el estado visual
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
            "nombre": etapa.nombre,
            "presupuesto": presupuesto,
            "gasto": gasto,
            "porcentaje": porcentaje,
            "estado": estado,
        })

    return resultado
