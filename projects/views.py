from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Project, Worker, Role, BudgetSection, BudgetItem, ProjectBudgetItem
from .forms import ProjectForm, WorkerForm, RoleForm, ConsumoMaterialForm, DetailedProjectForm, BudgetSectionForm, BudgetManagementForm
import json
from django.urls import reverse
from .models import Project, EntradaMaterial
from .forms import EntradaMaterialForm
from users.decorators import role_required, project_owner_or_jefe_required
from users.models import User
from django.core.exceptions import PermissionDenied

@project_owner_or_jefe_required
def registrar_entrada_material(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        form = EntradaMaterialForm(request.POST)
        if form.is_valid():
            entrada = form.save(commit=False)
            entrada.proyecto = project
            entrada.save()

            # Verificar si hay un consumo pendiente en la sesión (RF17D)
            consumo_pendiente = request.session.get('consumo_pendiente')

            if consumo_pendiente:
                try:
                    # Intentar registrar el consumo pendiente automáticamente
                    from .models import ConsumoMaterial
                    from catalog.models import Material

                    material = Material.objects.get(id=consumo_pendiente['material_id'])

                    # Crear el consumo con los datos guardados
                    consumo = ConsumoMaterial(
                        proyecto=project,
                        material=material,
                        cantidad_consumida=consumo_pendiente['cantidad_consumida'],
                        fecha_consumo=consumo_pendiente['fecha_consumo'],
                        componente_actividad=consumo_pendiente['componente_actividad'],
                        responsable=consumo_pendiente['responsable'],
                        observaciones=consumo_pendiente.get('observaciones', ''),
                        registrado_por=request.user
                    )

                    # Intentar guardar (validará stock nuevamente)
                    consumo.save()

                    # Limpiar la sesión
                    del request.session['consumo_pendiente']

                    messages.success(
                        request,
                        f'✅ Compra registrada exitosamente. '
                        f'✅ Consumo registrado automáticamente: {consumo.cantidad_consumida} {material.unit.symbol} '
                        f'de {material.name} para {consumo.componente_actividad}'
                    )

                except Exception as e:
                    # Si falla el registro del consumo, solo mostrar advertencia
                    messages.warning(
                        request,
                        f'✅ Compra registrada exitosamente. '
                        f'⚠️ No se pudo registrar el consumo automáticamente: {str(e)}. '
                        f'Por favor, regístralo manualmente.'
                    )
                    # Limpiar la sesión de todos modos
                    if 'consumo_pendiente' in request.session:
                        del request.session['consumo_pendiente']
            else:
                # No hay consumo pendiente, solo mensaje de compra exitosa
                messages.success(request, f'✅ Compra de {entrada.material.name} registrada exitosamente.')

            return redirect("projects:project_board", project_id=project.id)
    else:
        form = EntradaMaterialForm()

        # Verificar si hay un consumo pendiente para mostrar un aviso
        consumo_pendiente = request.session.get('consumo_pendiente')
        if consumo_pendiente:
            try:
                from catalog.models import Material
                material = Material.objects.get(id=consumo_pendiente['material_id'])
                messages.info(
                    request,
                    f'ℹ️ Después de registrar esta compra, se agregará automáticamente el consumo de '
                    f'{consumo_pendiente["cantidad_consumida"]} {material.unit.symbol} de {material.name}.'
                )
            except:
                pass

    return render(request, "projects/registrar_entrada_material.html", {"form": form, "project": project})

@role_required(User.CONSTRUCTOR, User.JEFE)
def project_list(request):
    """
    Vista para listar proyectos
    - COMERCIAL: Ve todos los proyectos (solo lectura, info básica)
    - CONSTRUCTOR: Ve todos los proyectos (solo edita los suyos)
    - JEFE: Ve y puede editar todos los proyectos
    """
    # Obtener parámetros de búsqueda desde la URL
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    ubicacion_filter = request.GET.get("ubicacion", "")
    pisos_filter = request.GET.get("pisos", "")
    acabados_filter = request.GET.get("acabados", "")
    area_min_filter = request.GET.get("area_min", "")
    area_max_filter = request.GET.get("area_max", "")
    presupuesto_min_filter = request.GET.get("presupuesto_min", "")
    presupuesto_max_filter = request.GET.get("presupuesto_max", "")
    terreno_filter = request.GET.get("terreno", "")
    acceso_filter = request.GET.get("acceso", "")
    banos_filter = request.GET.get("banos", "")
    fecha_desde_filter = request.GET.get("fecha_desde", "")
    fecha_hasta_filter = request.GET.get("fecha_hasta", "")
    creador_filter = request.GET.get("creador", "")

    # TODOS los usuarios ven TODOS los proyectos
    projects = Project.objects.all()

    # Filtro por búsqueda - PostgreSQL: LIKE queries para búsqueda de texto
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query)  # Buscar en nombre
            | Q(description__icontains=search_query)  # Buscar en descripción
            | Q(location_address__icontains=search_query)  # Buscar en dirección
        )

    # Filtro por estado - PostgreSQL: WHERE estado = [status_filter]
    if status_filter:
        projects = projects.filter(estado=status_filter)

    # Filtro por ubicación
    if ubicacion_filter:
        projects = projects.filter(ubicacion_proyecto=ubicacion_filter)

    # Filtro por número de pisos
    if pisos_filter:
        projects = projects.filter(numero_pisos=pisos_filter)

    # Filtro por nivel de acabados
    if acabados_filter:
        projects = projects.filter(acabado_muros=acabados_filter)

    # Filtro por área mínima
    if area_min_filter:
        try:
            area_min = float(area_min_filter)
            projects = projects.filter(area_construida_total__gte=area_min)
        except ValueError:
            pass

    # Filtro por área máxima
    if area_max_filter:
        try:
            area_max = float(area_max_filter)
            projects = projects.filter(area_construida_total__lte=area_max)
        except ValueError:
            pass

    # Filtro por presupuesto mínimo
    if presupuesto_min_filter:
        try:
            presupuesto_min = float(presupuesto_min_filter)
            projects = projects.filter(presupuesto__gte=presupuesto_min)
        except ValueError:
            pass

    # Filtro por presupuesto máximo
    if presupuesto_max_filter:
        try:
            presupuesto_max = float(presupuesto_max_filter)
            projects = projects.filter(presupuesto__lte=presupuesto_max)
        except ValueError:
            pass

    # Filtro por tipo de terreno
    if terreno_filter:
        projects = projects.filter(tipo_terreno=terreno_filter)

    # Filtro por acceso a obra
    if acceso_filter:
        projects = projects.filter(acceso_obra=acceso_filter)

    # Filtro por número de baños
    if banos_filter:
        try:
            banos_count = int(banos_filter)
            if banos_count == 3:
                # Para 3+, filtrar por 3 o más
                projects = projects.filter(numero_banos__gte=3)
            else:
                projects = projects.filter(numero_banos=banos_count)
        except ValueError:
            pass

    # Filtro por fecha desde
    if fecha_desde_filter:
        projects = projects.filter(fecha_creacion__gte=fecha_desde_filter)

    # Filtro por fecha hasta
    if fecha_hasta_filter:
        projects = projects.filter(fecha_creacion__lte=fecha_hasta_filter)

    # Filtro por creador
    if creador_filter:
        try:
            creador_id = int(creador_filter)
            projects = projects.filter(creado_por_id=creador_id)
        except ValueError:
            pass

    # Agrupar por estado para mostrar en secciones separadas
    # PostgreSQL: Múltiples consultas SELECT con filtros diferentes
    projects_en_proceso = projects.filter(estado="en_proceso")
    projects_terminados = projects.filter(estado="terminado")
    projects_futuros = projects.filter(estado="futuro")

    # Obtener lista de creadores únicos para el filtro
    creadores = User.objects.filter(
        id__in=Project.objects.values_list('creado_por_id', flat=True).distinct()
    ).order_by('first_name', 'last_name')

    # Verificar si hay filtros activos
    has_active_filters = any(
        [
            search_query,
            status_filter,
            ubicacion_filter,
            pisos_filter,
            acabados_filter,
            area_min_filter,
            area_max_filter,
            presupuesto_min_filter,
            presupuesto_max_filter,
            terreno_filter,
            acceso_filter,
            banos_filter,
            fecha_desde_filter,
            fecha_hasta_filter,
            creador_filter,
        ]
    )

    context = {
        "projects_en_proceso": projects_en_proceso,
        "projects_terminados": projects_terminados,
        "projects_futuros": projects_futuros,
        "search_query": search_query,
        "status_filter": status_filter,
        "ubicacion_filter": ubicacion_filter,
        "pisos_filter": pisos_filter,
        "acabados_filter": acabados_filter,
        "area_min_filter": area_min_filter,
        "area_max_filter": area_max_filter,
        "presupuesto_min_filter": presupuesto_min_filter,
        "presupuesto_max_filter": presupuesto_max_filter,
        "terreno_filter": terreno_filter,
        "acceso_filter": acceso_filter,
        "banos_filter": banos_filter,
        "fecha_desde_filter": fecha_desde_filter,
        "fecha_hasta_filter": fecha_hasta_filter,
        "creador_filter": creador_filter,
        "creadores": creadores,
        "has_active_filters": has_active_filters,
    }

    return render(request, "projects/project_list.html", context)


@login_required
@login_required
def project_board(request, project_id):
    """
    Vista tablero del proyecto: nombre, presupuesto, calendario, botones y listado de compras.
    - JEFE: Siempre accede al tablero (todos los proyectos)
    - CONSTRUCTOR: Solo accede al tablero si él creó el proyecto
    """
    # Obtener proyecto con sus entradas relacionadas a material y proveedor
    project = get_object_or_404(
        Project.objects.prefetch_related(
            'entradas__material', 
            'entradas__proveedor'
        ),
        id=project_id
    )

    # Verificar permisos: JEFE siempre puede, otros solo si crearon el proyecto
    if request.user.role != User.JEFE and not request.user.is_superuser:
        if project.creado_por != request.user:
            # Si no es JEFE y no creó el proyecto, redirigir a detalles
            return redirect('projects:project_detail', project_id=project.id)

    # Entradas de materiales del proyecto
    entradas_raw = project.entradas.all().order_by('material__name', '-fecha_ingreso')

    # Importar el modelo de consumos
    from .models import ConsumoMaterial, ProyectoMaterial

    # Agrupar por material
    from collections import defaultdict
    materiales_agrupados = defaultdict(lambda: {
        'material': None,
        'entradas': [],
        'cantidad_total': 0,
        'stock_proyecto': 0,
        'consumos': [],
        'cantidad_consumida': 0
    })

    for entrada in entradas_raw:
        material_id = entrada.material.id

        if materiales_agrupados[material_id]['material'] is None:
            materiales_agrupados[material_id]['material'] = entrada.material

            # Obtener consumos de este material en este proyecto
            consumos = ConsumoMaterial.objects.filter(
                proyecto=project,
                material=entrada.material
            ).select_related('registrado_por').order_by('-fecha_consumo')

            materiales_agrupados[material_id]['consumos'] = list(consumos)
            materiales_agrupados[material_id]['cantidad_consumida'] = sum(
                c.cantidad_consumida for c in consumos
            )

        materiales_agrupados[material_id]['entradas'].append(entrada)
        materiales_agrupados[material_id]['cantidad_total'] += entrada.cantidad

    # Calcular el stock correcto para cada material después de sumar todas las entradas
    for material_id, data in materiales_agrupados.items():
        # Stock = Total comprado - Total consumido
        data['stock_proyecto'] = data['cantidad_total'] - data['cantidad_consumida']

    # Convertir a lista para el template
    compras = list(materiales_agrupados.values())

    context = {
        "project": project,
        "compras": compras,
        "details_url": reverse("projects:project_detail", kwargs={"project_id": project.id}),
        "add_purchases_url": reverse("projects:registrar_entrada_material", kwargs={"project_id": project.id}),
        "charts_url": f"/proyectos/{project.id}/graficos/",
    }

    return render(request, "projects/project_board.html", context)


@login_required
def project_create(request):
    """
    Vista para crear un nuevo proyecto
    - COMERCIAL: Solo puede crear (después no podrá verlo en la lista)
    - CONSTRUCTOR: Redirige al formulario detallado
    - JEFE: Redirige al formulario detallado
    """
    # Redirigir JEFE y CONSTRUCTOR al formulario detallado
    if request.user.role in [User.JEFE, User.CONSTRUCTOR]:
        return redirect("projects:detailed_project_create")
    
    # Solo COMERCIAL usa el formulario simple
    workers = Worker.objects.all()
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES)
        selected_workers = request.POST.getlist("workers")
        if form.is_valid():
            try:
                project = form.save(commit=False)
                project.creado_por = request.user

                from decimal import Decimal
                project.built_area = project.area_construida_total or Decimal("0")
                project.exterior_area = project.area_exterior_intervenir or Decimal("0")
                project.columns_count = project.columns_count or 0
                project.walls_area = project.walls_area or Decimal("0")
                project.windows_area = project.windows_area or Decimal("0")
                project.doors_count = project.doors_count or 0
                project.doors_height = Decimal("2.1")

                project.save()
                project.calculate_legacy_fields()
                project.presupuesto = project.calculate_final_budget()
                project.save()

                if selected_workers:
                    project.workers.set(selected_workers)

                messages.success(
                    request,
                    f'✅ Proyecto "{project.name}" creado exitosamente! Presupuesto estimado: ${project.presupuesto:,.0f}',
                )

                # Redirigir según el rol
                if request.user.role == User.COMERCIAL:
                    # COMERCIAL no puede ver el detalle, mostrar mensaje y redirigir a crear otro
                    messages.info(request, "Proyecto creado. Puedes crear otro presupuesto.")
                    return redirect("projects:project_create")
                else:
                    return redirect("projects:project_detail", project_id=project.id)

            except Exception as e:
                messages.error(request, f"❌ Error al crear el proyecto: {str(e)}")
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        form = ProjectForm()

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "workers": workers,
            "no_workers": not workers.exists(),
        },
    )





@login_required
def project_detail(request, project_id):
    """
    Vista para mostrar el detalle de un proyecto
    Accesible para todos los usuarios autenticados
    """
    # Obtener proyecto sin restricción de creador
    project = get_object_or_404(Project, id=project_id)

    # Entradas de materiales del proyecto
    compras = project.entradas.select_related("material", "proveedor").all()
    print("DEBUG compras:", compras)


    # Agregar stock por proyecto a cada entrada
    for compra in compras:
        # Suponiendo que Material tiene un método stock_en_proyecto(project)
        pm = compra.material.proyectos.filter(proyecto=project).first()
        compra.stock_proyecto = pm.stock_proyecto if pm else 0

    # Calcular presupuesto estimado usando los datos del proyecto
    # Primero recalcular campos heredados para asegurar consistencia
    project.calculate_legacy_fields()
    estimated_budget = project.calculate_final_budget()
    
    context = {
        'project': project,
        'compras': compras,
        'estimated_budget': estimated_budget,
    }

    return render(request, "projects/project_detail.html", context)




@login_required
def project_update(request, project_id):
    """
    Vista para actualizar un proyecto
    PostgreSQL: UPDATE projects_project SET ... WHERE id = [project_id]
    """
    # Obtener proyecto específico del usuario actual
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)

    workers = Worker.objects.all()
    if request.method == "POST":
        # Procesar formulario with datos existentes
        form = ProjectForm(request.POST, request.FILES, instance=project)
        selected_workers = request.POST.getlist("workers")
        if form.is_valid():
            try:
                # Actualizar en PostgreSQL
                form.save()
                # Calcular campos heredados automáticamente
                project.calculate_legacy_fields()
                # Calcular presupuesto actualizado
                project.presupuesto = project.calculate_final_budget()
                # Guardar con los campos calculados
                project.save()
                # Actualizar trabajadores asignados
                if selected_workers:
                    project.workers.set(selected_workers)
                else:
                    project.workers.clear()
                messages.success(request, "Proyecto actualizado exitosamente!")
                return redirect("projects:project_detail", project_id=project.id)
            except Exception as e:
                messages.error(request, f"❌ Error al actualizar el proyecto: {str(e)}")
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        # Mostrar formulario con datos existentes
        form = ProjectForm(instance=project)

    return render(
        request,
        "projects/project_form.html",
        {
            "form": form,
            "project": project,
            "is_update": True,
            "workers": workers,
            "no_workers": not workers.exists(),
        },
    )


@project_owner_or_jefe_required
def project_delete(request, project_id):
    """
    Vista para eliminar un proyecto
    - CONSTRUCTOR: Solo puede eliminar SUS proyectos
    - JEFE: Puede eliminar cualquier proyecto
    - COMERCIAL: Sin acceso
    """
    # Obtener proyecto (el decorador ya verificó los permisos)
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Proyecto eliminado exitosamente!")
        return redirect("projects:project_list")

    return render(request, "projects/project_confirm_delete.html", {"project": project})


@login_required
def update_project_status(request, project_id):
    """
    Vista para actualizar el estado del proyecto (AJAX y POST)
    PostgreSQL: UPDATE projects_project SET estado = [new_status] WHERE id = [project_id]
    """
    if request.method == "POST":
        try:
            # Obtener proyecto
            project = get_object_or_404(Project, id=project_id, creado_por=request.user)

            # Verificar si es AJAX o formulario normal
            if request.content_type == "application/json":
                # Petición AJAX
                data = json.loads(request.body)
                new_status = data.get("status")
            else:
                # Formulario normal
                new_status = request.POST.get("status")

            # Validar estado
            valid_states = ["futuro", "en_proceso", "terminado"]
            if new_status not in valid_states:
                if request.content_type == "application/json":
                    return JsonResponse({"success": False, "error": "Estado inválido"})
                else:
                    messages.error(request, "❌ Estado inválido")
                    return redirect("projects:project_detail", project_id=project.id)

            # Actualizar estado
            project.estado = new_status
            project.save()

            # Responder según el tipo de petición
            if request.content_type == "application/json":
                return JsonResponse({"success": True, "status": new_status})
            else:
                messages.success(
                    request,
                    f'✅ Estado cambiado a "{project.get_estado_display()}" exitosamente',
                )
                return redirect("projects:project_detail", project_id=project.id)

        except Exception as e:
            if request.content_type == "application/json":
                return JsonResponse({"success": False, "error": str(e)})
            else:
                messages.error(request, f"❌ Error al cambiar estado: {str(e)}")
                return redirect("projects:project_detail", project_id=project.id)

    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
def recalculate_legacy_fields(request, project_id):
    """
    Vista para recalcular campos heredados de un proyecto específico via AJAX
    """
    if request.method == "POST":
        try:
            # Obtener proyecto
            project = get_object_or_404(Project, id=project_id, creado_por=request.user)

            # Calcular campos heredados
            project.calculate_legacy_fields()

            # Calcular presupuesto actualizado usando el método correcto
            project.presupuesto = project.calculate_final_budget()

            # Guardar cambios
            project.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Campos recalculados exitosamente",
                    "data": {
                        "walls_area": float(project.walls_area),
                        "windows_area": float(project.windows_area),
                        "doors_count": project.doors_count,
                        "presupuesto": float(project.presupuesto),
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
def project_view(request):
    """
    Vista para mostrar proyectos con diseño de cards responsive
    """
    # Obtener el término de búsqueda
    search_query = request.GET.get("search", "")

    # Filtrar proyectos del usuario actual
    projects = Project.objects.filter(creado_por=request.user)

    # Aplicar búsqueda si se proporciona un término
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query)  # Buscar en nombre
            | Q(description__icontains=search_query)  # Buscar en descripción
            | Q(location_address__icontains=search_query)  # Buscar en dirección
        )

    context = {
        "projects": projects,
        "search_query": search_query,
    }

    return render(request, "projects/project_view.html", context)


@login_required
def worker_create(request):
    """
    Vista para crear un nuevo trabajador
    PostgreSQL: INSERT INTO projects_worker (...) VALUES (...)
    """
    if request.method == "POST":
        form = WorkerForm(request.POST)
        if form.is_valid():
            try:
                # Crear trabajador pero no guardar aún
                worker = form.save(commit=False)

                # Guardar en PostgreSQL
                worker.save()

                messages.success(
                    request, f'✅ Trabajador "{worker.name}" creado exitosamente!'
                )
                return redirect("projects:worker_list")
            except Exception as e:
                messages.error(request, f"❌ Error al crear el trabajador: {str(e)}")
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        form = WorkerForm()
    return render(request, "projects/worker_form.html", {"form": form})


@login_required
def role_create(request):
    """
    Vista para crear un nuevo rol
    PostgreSQL: INSERT INTO projects_role (...) VALUES (...)
    """
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            try:
                # Crear rol pero no guardar aún
                role = form.save(commit=False)

                # Guardar en PostgreSQL
                role.save()

                messages.success(request, f'✅ Rol "{role.name}" creado exitosamente!')
                return redirect("projects:role_list")
            except Exception as e:
                messages.error(request, f"❌ Error al crear el rol: {str(e)}")
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        form = RoleForm()
    return render(request, "projects/role_form.html", {"form": form})


@login_required
def role_update(request, role_id):
    """
    Vista para actualizar un rol
    PostgreSQL: UPDATE projects_role SET ... WHERE id = [role_id]
    """
    role = get_object_or_404(Role, id=role_id)
    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f'Rol "{role.name}" actualizado exitosamente!')
            return redirect("projects:role_list")
    else:
        form = RoleForm(instance=role)
    return render(
        request,
        "projects/role_form.html",
        {"form": form, "role": role, "is_update": True},
    )


@login_required
def worker_list(request):
    """
    Vista para listar todos los trabajadores
    PostgreSQL: SELECT * FROM projects_worker
    """
    workers = Worker.objects.all()
    return render(request, "projects/worker_list.html", {"workers": workers})


@login_required
def role_list(request):
    """
    Vista para listar todos los roles
    PostgreSQL: SELECT * FROM projects_role
    """
    roles = Role.objects.all()
    return render(request, "projects/role_list.html", {"roles": roles})


@login_required
def worker_delete(request, worker_id):
    """
    Vista para eliminar un trabajador
    PostgreSQL: DELETE FROM projects_worker WHERE id = [worker_id]
    """
    worker = get_object_or_404(Worker, id=worker_id)
    if request.method == "POST":
        worker.delete()
        messages.success(request, f'Trabajador "{worker.name}" eliminado exitosamente!')
        return redirect('projects:worker_list')
    return render(request, 'projects/worker_confirm_delete.html', {'worker': worker})

@login_required
def role_delete(request, role_id):
    """
    Vista para eliminar un rol
    PostgreSQL: DELETE FROM projects_role WHERE id = [role_id]
    """
    role = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        role.delete()
        messages.success(request, f'Rol "{role.name}" eliminado exitosamente!')
        return redirect('projects:role_list')
    return render(request, 'projects/role_confirm_delete.html', {'role': role})

@login_required
def editar_entrada_material(request, entrada_id):
    entrada = get_object_or_404(EntradaMaterial, id=entrada_id, proyecto__creado_por=request.user)
    
    if request.method == "POST":
        form = EntradaMaterialForm(request.POST, instance=entrada)
        if form.is_valid():
            form.save()
            messages.success(request, f'Entrada de {entrada.material.nombre} actualizada correctamente.')
            return redirect("projects:project_board", project_id=entrada.proyecto.id)
    else:
        form = EntradaMaterialForm(instance=entrada)
    
    return render(request, "projects/editar_entrada_material.html", {"form": form, "entrada": entrada})

@login_required
def borrar_entrada_material(request, entrada_id):
    """
    Borra una entrada de material y muestra un mensaje de éxito.
    """
    entrada = get_object_or_404(EntradaMaterial, id=entrada_id)

    if request.method == "POST":
        material_name = entrada.material.name  # usa el campo correcto
        entrada.delete()
        messages.success(
            request, f'Entrada de {material_name} eliminada correctamente.'
        )
        return redirect('projects:project_board', project_id=entrada.proyecto.id)
    
    # Redirige al tablero si se accede con GET
    return redirect('projects:project_board', project_id=entrada.proyecto.id)


# ===== VISTAS PARA CONSUMO DIARIO DE MATERIALES (RF17A) =====

@login_required
def registrar_consumo_material(request, project_id):
    """
    Vista para registrar el consumo diario de materiales (RF17A)
    Con validación de stock insuficiente (RF17D)
    Se accede desde el calendario al seleccionar una fecha
    """
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)

    # Obtener fecha seleccionada del parámetro GET o usar hoy
    from django.utils import timezone
    fecha_seleccionada = request.GET.get('fecha', timezone.now().date())

    # Variables para manejar el error de stock insuficiente
    stock_insuficiente = False
    stock_disponible = None
    material_info = None

    if request.method == 'POST':
        form = ConsumoMaterialForm(request.POST, proyecto=project)

        if form.is_valid():
            try:
                consumo = form.save(commit=False)
                consumo.proyecto = project
                consumo.registrado_por = request.user
                consumo.save()

                messages.success(
                    request,
                    f'✅ Consumo registrado correctamente: {consumo.cantidad_consumida} {consumo.material.unit.symbol} '
                    f'de {consumo.material.name} para {consumo.componente_actividad}'
                )
                return redirect('projects:project_board', project_id=project.id)

            except Exception as e:
                messages.error(request, f'❌ Error al registrar consumo: {str(e)}')
        else:
            # Verificar si el error es de stock insuficiente (RF17D)
            if '__all__' in form.errors:
                error_msg = str(form.errors['__all__'][0])
                if 'Stock insuficiente' in error_msg:
                    stock_insuficiente = True
                    # Obtener información del stock desde el formulario
                    if hasattr(form, 'stock_disponible'):
                        stock_disponible = form.stock_disponible
                        material_info = {
                            'nombre': form.material_nombre,
                            'unidad': form.material_unidad,
                        }

                    messages.warning(request, f'⚠️ {error_msg}')
                else:
                    messages.error(request, error_msg)
            else:
                # Mostrar otros errores del formulario
                for field, errors in form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, f'{error}')
                        else:
                            messages.error(request, f'{field}: {error}')
    else:
        # Inicializar formulario with fecha seleccionada
        initial_data = {'fecha_consumo': fecha_seleccionada}
        form = ConsumoMaterialForm(initial=initial_data, proyecto=project)

    context = {
        'form': form,
        'project': project,
        'fecha_seleccionada': fecha_seleccionada,
        'stock_insuficiente': stock_insuficiente,
        'stock_disponible': stock_disponible,
        'material_info': material_info,
        'add_purchases_url': reverse("projects:registrar_entrada_material", kwargs={"project_id": project.id}),
    }

    return render(request, 'projects/registrar_consumo_material.html', context)


@login_required
def listar_consumos_proyecto(request, project_id):
    """
    Vista para listar todos los consumos de un proyecto
    Permite filtrar por fecha, material, actividad
    """
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)

    # Obtener parámetros de filtro
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    material_id = request.GET.get('material', '')
    actividad = request.GET.get('actividad', '')

    # Consulta base
    from .models import ConsumoMaterial
    consumos = ConsumoMaterial.objects.filter(
        proyecto=project
    ).select_related('material', 'material__unit', 'registrado_por')

    # Aplicar filtros
    if fecha_desde:
        consumos = consumos.filter(fecha_consumo__gte=fecha_desde)
    if fecha_hasta:
        consumos = consumos.filter(fecha_consumo__lte=fecha_hasta)
    if material_id:
        consumos = consumos.filter(material_id=material_id)
    if actividad:
        consumos = consumos.filter(componente_actividad__icontains=actividad)

    # Obtener lista de materiales para el filtro
    from catalog.models import Material
    materiales_usados = Material.objects.filter(
        consumos__proyecto=project
    ).distinct().order_by('name')

    context = {
        'project': project,
        'consumos': consumos,
        'materiales_usados': materiales_usados,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'material_id': material_id,
        'actividad': actividad,
    }

    return render(request, 'projects/listar_consumos.html', context)


@login_required
def obtener_consumos_fecha(request, project_id):
    """
    API endpoint para obtener consumos de una fecha específica (para el calendario)
    Retorna JSON con los consumos de la fecha
    """
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)
    fecha = request.GET.get('fecha')

    if not fecha:
        return JsonResponse({'error': 'Fecha no proporcionada'}, status=400)

    from .models import ConsumoMaterial
    consumos = ConsumoMaterial.objects.filter(
        proyecto=project,
        fecha_consumo=fecha
    ).select_related('material', 'material__unit').values(
        'id',
        'material__name',
        'material__sku',
        'cantidad_consumida',
        'material__unit__symbol',
        'componente_actividad',
        'responsable',
        'observaciones'
    )

    return JsonResponse({
        'fecha': fecha,
        'consumos': list(consumos),
        'total': consumos.count()
    })


@login_required
def obtener_consumos_mes(request, project_id):
    """
    API endpoint para obtener todos los consumos de un mes específico (RF17C)
    Retorna JSON con los consumos agrupados por fecha para el calendario
    """
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    if not mes or not anio:
        return JsonResponse({'error': 'Mes y año requeridos'}, status=400)

    try:
        mes = int(mes)
        anio = int(anio)
    except ValueError:
        return JsonResponse({'error': 'Mes y año deben ser números'}, status=400)

    from .models import ConsumoMaterial
    from datetime import date
    from collections import defaultdict

    # Obtener primer y último día del mes
    primer_dia = date(anio, mes, 1)
    if mes == 12:
        ultimo_dia = date(anio + 1, 1, 1)
    else:
        ultimo_dia = date(anio, mes + 1, 1)

    # Consultar consumos del mes
    consumos = ConsumoMaterial.objects.filter(
        proyecto=project,
        fecha_consumo__gte=primer_dia,
        fecha_consumo__lt=ultimo_dia
    ).select_related('material', 'material__unit').order_by('fecha_consumo')

    # Agrupar por fecha
    consumos_por_fecha = defaultdict(list)
    for consumo in consumos:
        fecha_str = consumo.fecha_consumo.strftime('%Y-%m-%d')
        consumos_por_fecha[fecha_str].append({
            'id': consumo.id,
            'material': consumo.material.name,
            'cantidad': float(consumo.cantidad_consumida),
            'unidad': consumo.material.unit.symbol,
            'actividad': consumo.componente_actividad,
            'responsable': consumo.responsable
        })

    return JsonResponse({
        'mes': mes,
        'anio': anio,
        'consumos_por_fecha': dict(consumos_por_fecha),
        'total_dias_con_registro': len(consumos_por_fecha)
    })


@login_required
def editar_consumo_material(request, consumo_id):
    """
    Vista para editar un consumo existente
    """
    from .models import ConsumoMaterial
    consumo = get_object_or_404(
        ConsumoMaterial,
        id=consumo_id,
        proyecto__creado_por=request.user
    )
    project = consumo.proyecto

    if request.method == 'POST':
        form = ConsumoMaterialForm(request.POST, instance=consumo, proyecto=project)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Consumo actualizado correctamente.')
                return redirect('projects:listar_consumos_proyecto', project_id=project.id)
            except Exception as e:
                messages.error(request, f'Error al actualizar consumo: {str(e)}')
    else:
        form = ConsumoMaterialForm(instance=consumo, proyecto=project)

    context = {
        'form': form,
        'project': project,
        'consumo': consumo,
        'is_edit': True,
    }

    return render(request, 'projects/registrar_consumo_material.html', context)


@login_required
def eliminar_consumo_material(request, consumo_id):
    """
    Vista para eliminar un consumo de material
    """
    from .models import ConsumoMaterial
    consumo = get_object_or_404(
        ConsumoMaterial,
        id=consumo_id,
        proyecto__creado_por=request.user
    )
    project_id = consumo.proyecto.id

    if request.method == 'POST':
        try:
            material_name = consumo.material.name
            cantidad = consumo.cantidad_consumida
            unidad = consumo.material.unit.symbol

            # Al eliminar, el stock se restaura automáticamente en el modelo
            consumo.delete()

            messages.success(
                request,
                f'✅ Consumo eliminado correctamente: {cantidad} {unidad} de {material_name}. El stock ha sido restaurado.'
            )
        except Exception as e:
            messages.error(
                request,
                f'❌ Error al eliminar el consumo: {str(e)}'
            )

        # Redirigir al tablero del proyecto
        return redirect('projects:project_board', project_id=project_id)

    # Si no es POST, también redirigir al tablero
    messages.warning(request, 'Método no permitido')
    return redirect('projects:project_board', project_id=project_id)


# VISTAS PARA PRESUPUESTO DETALLADO

@role_required(User.CONSTRUCTOR, User.JEFE)
@login_required
def detailed_project_create(request):
    """
    Vista para crear proyectos con presupuesto detallado completo
    Solo para CONSTRUCTOR y JEFE
    """
    sections = BudgetSection.objects.all().order_by('order')
    workers = Worker.objects.all()
    
    if request.method == "POST":
        # Procesar formulario básico del proyecto
        project_form = DetailedProjectForm(request.POST, request.FILES)
        selected_workers = request.POST.getlist("workers")
        
        if project_form.is_valid():
            try:
                # Crear el proyecto
                project = project_form.save(commit=False)
                project.creado_por = request.user
                
                # Establecer valores por defecto para campos obligatorios
                from decimal import Decimal
                project.built_area = Decimal("0")
                project.exterior_area = Decimal("0")
                project.columns_count = 0
                project.walls_area = Decimal("0")
                project.windows_area = Decimal("0")
                project.doors_count = 0
                project.doors_height = Decimal("2.1")
                
                project.save()
                
                # Asignar trabajadores si se seleccionaron
                if selected_workers:
                    project.workers.set(selected_workers)
                
                # Procesar cada sección del presupuesto (FUNCIONA)
                print("🔍 DEBUG: Iniciando procesamiento de presupuesto detallado")
                
                items_processed = 0
                for section in sections:
                    section_form = BudgetSectionForm(section, project, request.POST)
                    if section_form.is_valid():
                        section_form.save(project)
                        items_processed += 1
                        print(f"✅ Sección procesada: {section.name}")
                    else:
                        print(f"❌ Errores en sección {section.name}: {section_form.errors}")
                
                print(f"🔍 DEBUG: Total secciones procesadas: {items_processed}")
                
                # Calcular presupuesto total usando SOLO la suma de ítems detallados
                presupuesto_calculado = project.calculate_final_budget()
                project.presupuesto = presupuesto_calculado
                project.save()
                
                print(f"DEBUG: Presupuesto calculado: ${presupuesto_calculado:,.0f}")
                print(f"DEBUG: Total ProjectBudgetItems: {project.budget_items.count()}")
                
                messages.success(
                    request,
                    f'✅ Proyecto "{project.name}" creado exitosamente con presupuesto detallado! '
                    f'Presupuesto total: ${project.presupuesto:,.0f}'
                )
                
                return redirect("projects:detailed_budget_view", project_id=project.id)
                
            except Exception as e:
                messages.error(request, f"❌ Error al crear el proyecto: {str(e)}")
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        project_form = DetailedProjectForm()
    
    # Preparar formularios para cada sección
    section_forms = []
    for section in sections:
        form = BudgetSectionForm(section, None)  # Sin proyecto aún
        section_forms.append({
            'section': section,
            'form': form
        })

    return render(
        request,
        "projects/detailed_project_form.html",
        {
            "project_form": project_form,
            "section_forms": section_forms,
            "workers": workers,
            "no_workers": not workers.exists(),
        }
    )


@role_required(User.CONSTRUCTOR, User.JEFE)
@login_required
def detailed_budget_edit(request, project_id):
    """
    NUEVA VISTA SIMPLE: Editar presupuesto detallado
    """
    print(f"🔍 DEBUG: ===== INICIANDO detailed_budget_edit =====")
    print(f"🔍 DEBUG: Proyecto ID: {project_id}")
    print(f"🔍 DEBUG: Usuario: {request.user}")
    print(f"🔍 DEBUG: Rol usuario: {request.user.role}")
    
    project = get_object_or_404(Project, id=project_id)
    print(f"🔍 DEBUG: Proyecto encontrado: {project.name}")
    
    # Verificar permisos
    if request.user.role == User.CONSTRUCTOR and project.creado_por != request.user:
        print(f"🔍 DEBUG: ❌ Permisos denegados")
        raise PermissionDenied("No tienes permisos para editar este proyecto")
    
    print(f"🔍 DEBUG: ✅ Permisos verificados")
    print(f"🔍 DEBUG: Nueva vista simple para proyecto {project.id}")
    
    if request.method == "POST":
        print("🔍 DEBUG: Procesando formulario POST")
        
        # Procesar solo las cantidades que vienen en el POST
        items_updated = 0
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                item_id = key.replace('quantity_', '')
                try:
                    from decimal import Decimal
                    quantity = Decimal(str(value)) if value else Decimal('0')
                    if quantity > 0:
                        # Obtener el BudgetItem para usar su precio unitario
                        try:
                            budget_item = BudgetItem.objects.get(id=item_id)
                            
                            # Actualizar o crear ProjectBudgetItem
                            project_item, created = ProjectBudgetItem.objects.get_or_create(
                                project=project,
                                budget_item=budget_item,
                                defaults={
                                    'quantity': quantity,
                                    'unit_price': budget_item.unit_price
                                }
                            )
                            if not created:
                                project_item.quantity = quantity
                                project_item.unit_price = budget_item.unit_price
                                project_item.save()
                            items_updated += 1
                            print(f"✅ Actualizado ítem {item_id}: cantidad {quantity}, precio {budget_item.unit_price}")
                        except BudgetItem.DoesNotExist:
                            print(f"❌ BudgetItem {item_id} no existe")
                            continue
                except (ValueError, ProjectBudgetItem.DoesNotExist):
                    continue
        
        # Recalcular presupuesto
        presupuesto_calculado = project.calculate_final_budget()
        project.presupuesto = presupuesto_calculado
        project.save()
        
        print(f"🔍 DEBUG: {items_updated} ítems actualizados")
        print(f"🔍 DEBUG: Presupuesto recalculado: ${presupuesto_calculado:,.0f}")
        
        messages.success(request, f'✅ Presupuesto actualizado! {items_updated} ítems modificados.')
        return redirect("projects:detailed_budget_view", project_id=project.id)
    
    # Obtener TODAS las secciones (las 23)
    all_sections = BudgetSection.objects.all().order_by('order')
    
    # Obtener ítems configurados del proyecto
    project_items = ProjectBudgetItem.objects.filter(project=project).select_related(
        'budget_item__section'
    ).order_by('budget_item__section__order', 'budget_item__order')
    
    # Crear diccionario de ítems por ID para búsqueda rápida
    project_items_dict = {item.budget_item.id: item for item in project_items}
    
    # Preparar datos para TODAS las secciones
    sections_data = {}
    for section in all_sections:
        # Obtener todos los ítems de esta sección
        section_items = BudgetItem.objects.filter(section=section, is_active=True).order_by('order')
        
        # Preparar ítems para esta sección
        items_for_section = []
        for budget_item in section_items:
            # Verificar si este ítem está configurado en el proyecto
            project_item = project_items_dict.get(budget_item.id)
            
            if project_item:
                # Ya está configurado, usar valores del proyecto
                items_for_section.append({
                    'budget_item': budget_item,
                    'project_item': project_item,
                    'quantity': project_item.quantity,
                    'unit_price': project_item.unit_price,
                    'total_price': project_item.total_price,
                    'is_configured': True
                })
                print(f"🔍 DEBUG: Ítem configurado {budget_item.description[:30]}: cantidad={project_item.quantity}, precio={project_item.unit_price}")
            else:
                # No está configurado, usar valores por defecto
                items_for_section.append({
                    'budget_item': budget_item,
                    'project_item': None,
                    'quantity': 0,
                    'unit_price': budget_item.unit_price,
                    'total_price': 0,
                    'is_configured': False
                })
                print(f"🔍 DEBUG: Ítem no configurado {budget_item.description[:30]}: precio={budget_item.unit_price}")
        
        sections_data[section.id] = {
            'section': section,
            'items': items_for_section
        }
    
    print(f"🔍 DEBUG: {len(sections_data)} secciones totales (todas las 23)")
    print(f"🔍 DEBUG: {len(project_items)} ítems configurados en el proyecto")
    
    # Debug: Verificar datos antes de enviar al template
    print(f"🔍 DEBUG: Datos para el template:")
    for section_id, data in sections_data.items():
        print(f"  Sección {data['section'].order} ({data['section'].name}): {len(data['items'])} ítems")
        for item in data['items']:
            print(f"    - {item['budget_item'].description[:30]}: cantidad={item['quantity']}, precio={item['unit_price']}, total={item['total_price']}")
    
    try:
        context = {
            'project': project,
            'sections_data': sections_data,
            'total_budget': project.calculate_final_budget()
        }
        
        print(f"🔍 DEBUG: ===== RENDERIZANDO TEMPLATE =====")
        print(f"🔍 DEBUG: Secciones en context: {len(sections_data)}")
        print(f"🔍 DEBUG: Presupuesto total: ${project.calculate_final_budget():,.0f}")
        
        return render(request, "projects/simple_budget_edit.html", context)
        
    except Exception as e:
        print(f"❌ ERROR en detailed_budget_edit: {str(e)}")
        print(f"❌ Tipo de error: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        messages.error(request, f"❌ Error al cargar el presupuesto: {str(e)}")
        return redirect("projects:project_detail", project_id=project.id)


@role_required(User.CONSTRUCTOR, User.JEFE)
@login_required
def detailed_budget_view(request, project_id):
    """
    Vista para ver el presupuesto detallado de un proyecto
    OPTIMIZADA: Solo carga secciones con ítems configurados
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Verificar permisos
    if request.user.role == User.CONSTRUCTOR and project.creado_por != request.user:
        raise PermissionDenied("No tienes permisos para ver este proyecto")
    
    # OPTIMIZACIÓN: Solo cargar secciones que tienen ítems configurados
    sections = BudgetSection.objects.filter(
        items__projectbudgetitem__project=project
    ).distinct().order_by('order')
    
    # Obtener todos los ProjectBudgetItem del proyecto de una vez
    project_items_dict = {
        item.budget_item_id: item 
        for item in ProjectBudgetItem.objects.filter(project=project).select_related('budget_item')
    }
    
    section_data = []
    total_budget = 0
    
    for section in sections:
        items = []
        section_total = 0
        
        # Solo obtener ítems que están configurados en el proyecto
        section_items = BudgetItem.objects.filter(
            section=section, 
            is_active=True,
            projectbudgetitem__project=project
        ).order_by('order')
        
        for item in section_items:
            project_item = project_items_dict.get(item.id)
            item_total = project_item.total_price if project_item else 0
            
            items.append({
                'item': item,
                'project_item': project_item,
                'total': item_total
            })
            section_total += item_total
        
        section_data.append({
            'section': section,
            'items': items,
            'total': section_total
        })
        total_budget += section_total
    
    # ✅ USAR EL CÁLCULO CORRECTO QUE INCLUYE ADMINISTRACIÓN
    total_budget = project.calculate_final_budget()
    
    context = {
        'project': project,
        'section_data': section_data,
        'total_budget': total_budget
    }
    
    return render(request, "projects/detailed_budget_view.html", context)


@role_required(User.JEFE)
@login_required
def budget_management(request):
    """
    Vista para gestionar precios unitarios (solo JEFE)
    """
    sections = BudgetSection.objects.all().order_by('order')
    section_data = []
    
    for section in sections:
        items = BudgetItem.objects.filter(section=section).order_by('order')
        section_data.append({
            'section': section,
            'items': items
        })
    
    context = {
        'section_data': section_data
    }
    
    return render(request, "projects/budget_management.html", context)


@role_required(User.JEFE)
@login_required
def budget_item_update(request, item_id):
    """
    Vista para actualizar un ítem del presupuesto (solo JEFE)
    """
    item = get_object_or_404(BudgetItem, id=item_id)
    
    if request.method == "POST":
        form = BudgetManagementForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Ítem "{item.description[:50]}" actualizado exitosamente!')
            return redirect("projects:budget_management")
        else:
            messages.error(request, "❌ Por favor corrige los errores en el formulario")
    else:
        form = BudgetManagementForm(instance=item)
    
    context = {
        'item': item,
        'form': form
    }
    
    return render(request, "projects/budget_item_form.html", context)


def calculate_detailed_budget_total(project):
    """
    FUNCIÓN ESPECÍFICA PARA FORMULARIO DETALLADO
    Suma ítems del presupuesto + administración automática (12%)
    """
    from decimal import Decimal
    
    costo_directo = Decimal('0')
    administracion_manual = Decimal('0')
    
    # Separar costo directo de administración manual
    project_items = ProjectBudgetItem.objects.filter(project=project)
    for item in project_items:
        # Si es de la sección 21 (Administración), contarlo por separado
        if item.budget_item.section.order == 21:
            administracion_manual += item.total_price
        else:
            costo_directo += item.total_price
    
    # Calcular administración automática (12% sobre costo directo)
    administracion_automatica = costo_directo * Decimal('0.12')
    
    # Total = Costo Directo + Administración Automática + Administración Manual
    total = costo_directo + administracion_automatica + administracion_manual
    
    return total
