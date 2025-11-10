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


def duplicate_project(project):
    """
    Crea una copia completa de un proyecto existente.
    - Copia la información básica del proyecto
    - Copia los items del presupuesto
    - Genera un nombre único añadiendo "- Copia X"
    - Mantiene el estado como "futuro"
    """
    from .models import Project, ProjectBudgetItem
    from django.utils import timezone
    
    # Buscar copias existentes para generar el número correcto
    base_name = project.name
    copy_number = 1
    while Project.objects.filter(name=f"{base_name} - Copia {copy_number}").exists():
        copy_number += 1
    
    # Crear nueva instancia del proyecto sin guardar
    new_project = Project(
        name=f"{base_name} - Copia {copy_number}",
        description=project.description,
        location_address=project.location_address,
        area_construida_total=project.area_construida_total,
        area_exterior_intervenir=project.area_exterior_intervenir,
        columns_count=project.columns_count,
        walls_area=project.walls_area,
        windows_area=project.windows_area,
        doors_count=project.doors_count,
        doors_height=project.doors_height,
        built_area=project.built_area,
        exterior_area=project.exterior_area,
        presupuesto=project.presupuesto,
        administration_percentage=project.administration_percentage,
        creado_por=project.creado_por,
        estado='futuro',  # Siempre inicia como futuro
        fecha_creacion=timezone.now(),
        numero_banos=project.numero_banos,  # Copiar campos adicionales
        nivel_enchape_banos=project.nivel_enchape_banos
    )
    
    # Copiar imagen si existe
    if project.imagen_proyecto:
        from django.core.files import File
        from pathlib import Path
        import os
        
        # Crear nombre único para la imagen
        original_name = Path(project.imagen_proyecto.name).name
        name_parts = os.path.splitext(original_name)
        new_image_name = f"{name_parts[0]}_copia_{copy_number}{name_parts[1]}"
        
        # Abrir y copiar la imagen
        with project.imagen_proyecto.open() as img:
            new_project.imagen_proyecto.save(new_image_name, File(img), save=False)
    
    # Guardar el nuevo proyecto
    new_project.save()
    
    # Copiar trabajadores asociados
    new_project.workers.set(project.workers.all())
    
    # Copiar secciones de presupuesto específicas del proyecto
    from .models import BudgetSection
    original_sections = BudgetSection.objects.filter(project=project)
    new_sections = []
    for section in original_sections:
        new_section = BudgetSection.objects.create(
            project=new_project,
            name=section.name,
            order=section.order,
            description=section.description,
            is_percentage=section.is_percentage,
            percentage_value=section.percentage_value
        )
    
    # Copiar items del presupuesto
    budget_items = ProjectBudgetItem.objects.filter(project=project)
    new_budget_items = []
    
    for item in budget_items:
        new_budget_items.append(ProjectBudgetItem(
            project=new_project,
            budget_item=item.budget_item,
            quantity=item.quantity,
            unit_price=item.unit_price
        ))
    
    # Crear todos los items del presupuesto en una sola operación
    if new_budget_items:
        ProjectBudgetItem.objects.bulk_create(new_budget_items)
    
    # Copiar las entradas de material (stock)
    from .models import EntradaMaterial, ConsumoMaterial, ProyectoMaterial
    
    # Copiar entradas de material
    entradas = EntradaMaterial.objects.filter(proyecto=project)
    new_entradas = []
    for entrada in entradas:
        new_entradas.append(EntradaMaterial(
            proyecto=new_project,
            material=entrada.material,
            cantidad=entrada.cantidad,
            proveedor=entrada.proveedor,
            fecha_ingreso=entrada.fecha_ingreso
        ))
    if new_entradas:
        EntradaMaterial.objects.bulk_create(new_entradas)
    
    # Copiar consumos de material
    consumos = ConsumoMaterial.objects.filter(proyecto=project)
    new_consumos = []
    for consumo in consumos:
        new_consumos.append(ConsumoMaterial(
            proyecto=new_project,
            material=consumo.material,
            cantidad_consumida=consumo.cantidad_consumida,
            fecha_consumo=consumo.fecha_consumo,
            fecha_registro=timezone.now(),
            etapa_presupuesto=consumo.etapa_presupuesto,
            componente_actividad=consumo.componente_actividad,
            responsable=consumo.responsable,
            observaciones=consumo.observaciones,
            registrado_por=project.creado_por
        ))
    if new_consumos:
        ConsumoMaterial.objects.bulk_create(new_consumos)
    
    # Copiar stock de materiales del proyecto
    proyecto_materiales = ProyectoMaterial.objects.filter(proyecto=project)
    new_proyecto_materiales = []
    for pm in proyecto_materiales:
        new_proyecto_materiales.append(ProyectoMaterial(
            proyecto=new_project,
            material=pm.material,
            stock_proyecto=pm.stock_proyecto
        ))
    if new_proyecto_materiales:
        ProyectoMaterial.objects.bulk_create(new_proyecto_materiales)
    
    # Forzar el cálculo de campos heredados y presupuesto
    new_project.calculate_legacy_fields()
    new_project.presupuesto = new_project.calculate_final_budget()
    
    # Asegurarnos de que el presupuesto se guarde correctamente
    new_project.save()
    
    # Recalcular el presupuesto final teniendo en cuenta todas las secciones
    try:
        # Actualizar primero todos los totales de ProjectBudgetItem
        for item in ProjectBudgetItem.objects.filter(project=new_project):
            item.save()  # Esto recalculará total_price
        
        new_project.presupuesto = new_project.calculate_final_budget()
        new_project.presupuesto_gastado = 0  # Reiniciar el gasto ya que es un proyecto nuevo
        new_project.save()
        
    except Exception as e:
        print(f"Warning: Error al recalcular presupuesto final: {str(e)}")
    
    return new_project

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
