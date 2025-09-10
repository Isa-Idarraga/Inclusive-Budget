from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Project, Worker, Role
from .forms import ProjectForm, WorkerForm, RoleForm
import json
from django.urls import reverse
from .models import Project, EntradaMaterial
from .forms import EntradaMaterialForm

@login_required
def registrar_entrada_material(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        form = EntradaMaterialForm(request.POST)
        if form.is_valid():
            entrada = form.save(commit=False)
            entrada.proyecto = project
            entrada.save()
            return redirect("projects:project_board", project_id=project.id)  # vuelve al detalle del proyecto
    else:
        form = EntradaMaterialForm()

    return render(request, "projects/registrar_entrada_material.html", {"form": form, "project": project})

@login_required
def project_list(request):
    """
    Vista para listar todos los proyectos del usuario
    PostgreSQL: Realiza consultas SELECT con filtros y agrupación por estado
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

    # Consulta inicial: obtener proyectos del usuario actual
    # PostgreSQL: SELECT * FROM projects_project WHERE creado_por_id = [user_id]
    projects = Project.objects.filter(creado_por=request.user)

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

    # Agrupar por estado para mostrar en secciones separadas
    # PostgreSQL: Múltiples consultas SELECT con filtros diferentes
    projects_en_proceso = projects.filter(estado="en_proceso")
    projects_terminados = projects.filter(estado="terminado")
    projects_futuros = projects.filter(estado="futuro")

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
        "has_active_filters": has_active_filters,
    }

    return render(request, "projects/project_list.html", context)


@login_required
@login_required
def project_board(request, project_id):
    """
    Vista tablero del proyecto: nombre, presupuesto, calendario, botones y listado de compras.
    """
    # Obtener proyecto con sus entradas relacionadas a material y proveedor
    project = get_object_or_404(
        Project.objects.prefetch_related(
            'entradas__material', 
            'entradas__proveedor'
        ),
        id=project_id,
        creado_por=request.user
    )

    # Entradas de materiales del proyecto
    compras = project.entradas.all()

    # Agregar stock por proyecto a cada entrada
    for compra in compras:
        # Suponiendo que Material tiene un método stock_en_proyecto(project)
        pm = compra.material.proyectos.filter(proyecto=project).first()
        compra.stock_proyecto = pm.stock_proyecto if pm else 0

    context = {
        "project": project,
        "compras": compras,
        "details_url": reverse("projects:project_detail", kwargs={"project_id": project.id}),
        "add_purchases_url": reverse("projects:registrar_entrada_material", kwargs={"project_id": project.id}),
        "charts_url": f"/proyectos/{project.id}/graficos/",  # cámbialo si tienes URL real
    }

    return render(request, "projects/project_board.html", context)


@login_required
def project_create(request):
    """
    Vista para crear un nuevo proyecto
    PostgreSQL: INSERT INTO projects_project (...) VALUES (...)
    """
    workers = Worker.objects.all()
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES)
        selected_workers = request.POST.getlist("workers")
        if form.is_valid():
            try:
                # Crear proyecto pero no guardar aún
                project = form.save(commit=False)
                # Asignar usuario actual como creador
                project.creado_por = request.user

                # Asegurar que los campos heredados tengan valores por defecto
                from decimal import Decimal

                project.built_area = project.area_construida_total or Decimal("0")
                project.exterior_area = project.area_exterior_intervenir or Decimal("0")
                project.columns_count = project.columns_count or 0
                project.walls_area = project.walls_area or Decimal("0")
                project.windows_area = project.windows_area or Decimal("0")
                project.doors_count = project.doors_count or 0
                project.doors_height = Decimal("2.1")

                # Guardar en PostgreSQL primero
                project.save()
                # Calcular campos heredados automáticamente PRIMERO
                project.calculate_legacy_fields()
                # Calcular presupuesto automáticamente DESPUÉS
                project.presupuesto = project.calculate_detailed_budget()
                # Guardar nuevamente con el presupuesto y campos calculados
                project.save()
                # Asignar trabajadores seleccionados
                if selected_workers:
                    project.workers.set(selected_workers)
                messages.success(
                    request,
                    f'✅ Proyecto "{project.name}" creado exitosamente! Presupuesto estimado: ${project.presupuesto:,.0f}',
                )
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
    PostgreSQL: SELECT * FROM projects_project WHERE id = [project_id] AND creado_por_id = [user_id]
    """
    # Obtener proyecto específico del usuario actual
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)

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
    estimated_budget = project.calculate_detailed_budget()
    
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
        # Procesar formulario con datos existentes
        form = ProjectForm(request.POST, request.FILES, instance=project)
        selected_workers = request.POST.getlist("workers")
        if form.is_valid():
            try:
                # Actualizar en PostgreSQL
                form.save()
                # Calcular campos heredados automáticamente
                project.calculate_legacy_fields()
                # Calcular presupuesto actualizado
                project.presupuesto = project.calculate_detailed_budget()
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


@login_required
def project_delete(request, project_id):
    """
    Vista para eliminar un proyecto
    PostgreSQL: DELETE FROM projects_project WHERE id = [project_id]
    """
    # Obtener proyecto específico del usuario actual
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)

    if request.method == "POST":
        # Eliminar de PostgreSQL
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


def calculate_estimated_budget(project):
    """
    Función para calcular el presupuesto estimado usando el nuevo método detallado
    Usa precios unitarios configurables desde el admin
    """
    return project.calculate_detailed_budget()


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

            # Calcular presupuesto actualizado
            project.presupuesto = project.calculate_detailed_budget()

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
