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


@login_required
def project_list(request):
    """
    Vista para listar todos los proyectos del usuario
    PostgreSQL: Realiza consultas SELECT con filtros y agrupación por estado
    """
    # Obtener parámetros de búsqueda desde la URL
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Consulta inicial: obtener proyectos del usuario actual
    # PostgreSQL: SELECT * FROM projects_project WHERE creado_por_id = [user_id]
    projects = Project.objects.filter(creado_por=request.user)
    
    # Filtro por búsqueda - PostgreSQL: LIKE queries para búsqueda de texto
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |      # Buscar en nombre
            Q(description__icontains=search_query) | # Buscar en descripción
            Q(location_address__icontains=search_query) # Buscar en dirección
        )
    
    # Filtro por estado - PostgreSQL: WHERE estado = [status_filter]
    if status_filter:
        projects = projects.filter(estado=status_filter)
    
    # Agrupar por estado para mostrar en secciones separadas
    # PostgreSQL: Múltiples consultas SELECT con filtros diferentes
    projects_en_proceso = projects.filter(estado='en_proceso')
    projects_terminados = projects.filter(estado='terminado')
    projects_futuros = projects.filter(estado='futuro')
    
    context = {
        'projects_en_proceso': projects_en_proceso,
        'projects_terminados': projects_terminados,
        'projects_futuros': projects_futuros,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'projects/project_list.html', context)

@login_required
def project_board(request, project_id):
    """
    Vista tablero del proyecto: nombre, presupuesto, calendario, botones.
    """
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)

    context = {
        "project": project,
        # tú decides adónde llevan:
        "details_url": reverse("projects:project_detail", kwargs={"project_id": project.id}),
        "add_purchases_url": f"/compras/nueva/{project.id}/",  # cámbialo a tu ruta real
        "charts_url": f"/proyectos/{project.id}/graficos/",    # cámbialo a tu ruta real
    }
    return render(request, "projects/project_board.html", context)

@login_required
def project_create(request):
    """
    Vista para crear un nuevo proyecto
    PostgreSQL: INSERT INTO projects_project (...) VALUES (...)
    """
    workers = Worker.objects.all()
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        selected_workers = request.POST.getlist('workers')
        if form.is_valid():
            try:
                # Crear proyecto pero no guardar aún
                project = form.save(commit=False)
                # Asignar usuario actual como creador
                project.creado_por = request.user
                
                # Asegurar que los campos heredados tengan valores por defecto
                from decimal import Decimal
                
                project.built_area = project.area_construida_total or Decimal('0')
                project.exterior_area = project.area_exterior_intervenir or Decimal('0')
                project.columns_count = project.columns_count or 0
                project.walls_area = project.walls_area or Decimal('0')
                project.windows_area = project.windows_area or Decimal('0')
                project.doors_count = project.doors_count or 0
                project.doors_height = Decimal('2.1')
                
                # Guardar en PostgreSQL primero
                project.save()
                # Calcular presupuesto automáticamente
                project.presupuesto = project.calculate_detailed_budget()
                # Guardar nuevamente con el presupuesto
                project.save()
                # Asignar trabajadores seleccionados
                if selected_workers:
                    project.workers.set(selected_workers)
                messages.success(request, f'✅ Proyecto "{project.name}" creado exitosamente! Presupuesto estimado: ${project.presupuesto:,.0f}')
                return redirect('projects:project_detail', project_id=project.id)
            except Exception as e:
                messages.error(request, f'❌ Error al crear el proyecto: {str(e)}')
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {
        'form': form,
        'workers': workers,
        'no_workers': not workers.exists(),
    })

@login_required
def project_detail(request, project_id):
    """
    Vista para mostrar el detalle de un proyecto
    PostgreSQL: SELECT * FROM projects_project WHERE id = [project_id] AND creado_por_id = [user_id]
    """
    # Obtener proyecto específico del usuario actual
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)
    
    # Calcular presupuesto estimado usando los datos del proyecto
    estimated_budget = calculate_estimated_budget(project)
    
    context = {
        'project': project,
        'estimated_budget': estimated_budget,
    }
    
    return render(request, 'projects/project_detail.html', context)

@login_required
def project_update(request, project_id):
    """
    Vista para actualizar un proyecto
    PostgreSQL: UPDATE projects_project SET ... WHERE id = [project_id]
    """
    # Obtener proyecto específico del usuario actual
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)
    
    workers = Worker.objects.all()
    if request.method == 'POST':
        # Procesar formulario con datos existentes
        form = ProjectForm(request.POST, request.FILES, instance=project)
        selected_workers = request.POST.getlist('workers')
        if form.is_valid():
            # Actualizar en PostgreSQL
            form.save()
            # Actualizar trabajadores asignados
            if selected_workers:
                project.workers.set(selected_workers)
            else:
                project.workers.clear()
            messages.success(request, 'Proyecto actualizado exitosamente!')
            return redirect('projects:project_detail', project_id=project.id)
    else:
        # Mostrar formulario con datos existentes
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {
        'form': form, 
        'project': project,
        'is_update': True,
        'workers': workers,
        'no_workers': not workers.exists(),
    })

@login_required
def project_delete(request, project_id):
    """
    Vista para eliminar un proyecto
    PostgreSQL: DELETE FROM projects_project WHERE id = [project_id]
    """
    # Obtener proyecto específico del usuario actual
    project = get_object_or_404(Project, id=project_id, creado_por=request.user)
    
    if request.method == 'POST':
        # Eliminar de PostgreSQL
        project.delete()
        messages.success(request, 'Proyecto eliminado exitosamente!')
        return redirect('projects:project_list')
    
    return render(request, 'projects/project_confirm_delete.html', {'project': project})

@login_required
def update_project_status(request, project_id):
    """
    Vista para actualizar el estado del proyecto (AJAX y POST)
    PostgreSQL: UPDATE projects_project SET estado = [new_status] WHERE id = [project_id]
    """
    if request.method == 'POST':
        try:
            # Obtener proyecto
            project = get_object_or_404(Project, id=project_id, creado_por=request.user)
            
            # Verificar si es AJAX o formulario normal
            if request.content_type == 'application/json':
                # Petición AJAX
                data = json.loads(request.body)
                new_status = data.get('status')
            else:
                # Formulario normal
                new_status = request.POST.get('status')
            
            # Validar estado
            valid_states = ['futuro', 'en_proceso', 'terminado']
            if new_status not in valid_states:
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': 'Estado inválido'})
                else:
                    messages.error(request, '❌ Estado inválido')
                    return redirect('projects:project_detail', project_id=project.id)
            
            # Actualizar estado
            project.estado = new_status
            project.save()
            
            # Responder según el tipo de petición
            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'status': new_status})
            else:
                messages.success(request, f'✅ Estado cambiado a "{project.get_estado_display()}" exitosamente')
                return redirect('projects:project_detail', project_id=project.id)
                
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'❌ Error al cambiar estado: {str(e)}')
                return redirect('projects:project_detail', project_id=project.id)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def calculate_estimated_budget(project):
    """
    Función para calcular el presupuesto estimado usando el nuevo método detallado
    Usa precios unitarios configurables desde el admin
    """
    return project.calculate_detailed_budget()

@login_required
def project_view(request):
    """
    Vista para mostrar proyectos con diseño de cards responsive
    """
    # Obtener el término de búsqueda
    search_query = request.GET.get('search', '')
    
    # Filtrar proyectos del usuario actual
    projects = Project.objects.filter(creado_por=request.user)
    
    # Aplicar búsqueda si se proporciona un término
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |      # Buscar en nombre
            Q(description__icontains=search_query) | # Buscar en descripción
            Q(location_address__icontains=search_query) # Buscar en dirección
        )
    
    context = {
        'projects': projects,
        'search_query': search_query,
    }
    
    return render(request, 'projects/project_view.html', context)

@login_required
def worker_create(request):
    """
    Vista para crear un nuevo trabajador
    PostgreSQL: INSERT INTO projects_worker (...) VALUES (...)
    """
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            try:
                # Crear trabajador pero no guardar aún
                worker = form.save(commit=False)
                
                # Guardar en PostgreSQL
                worker.save()
                
                messages.success(request, f'✅ Trabajador "{worker.name}" creado exitosamente!')
                return redirect('projects:worker_list')
            except Exception as e:
                messages.error(request, f'❌ Error al crear el trabajador: {str(e)}')
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario')
    else:
        form = WorkerForm()
    return render(request, 'projects/worker_form.html', {'form': form})

@login_required
def role_create(request):
    """
    Vista para crear un nuevo rol
    PostgreSQL: INSERT INTO projects_role (...) VALUES (...)
    """
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            try:
                # Crear rol pero no guardar aún
                role = form.save(commit=False)
                
                # Guardar en PostgreSQL
                role.save()
                
                messages.success(request, f'✅ Rol "{role.name}" creado exitosamente!')
                return redirect('projects:role_list')
            except Exception as e:
                messages.error(request, f'❌ Error al crear el rol: {str(e)}')
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario')
    else:
        form = RoleForm()
    return render(request, 'projects/role_form.html', {'form': form})

@login_required
def role_update(request, role_id):
    """
    Vista para actualizar un rol
    PostgreSQL: UPDATE projects_role SET ... WHERE id = [role_id]
    """
    role = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f'Rol "{role.name}" actualizado exitosamente!')
            return redirect('projects:role_list')
    else:
        form = RoleForm(instance=role)
    return render(request, 'projects/role_form.html', {'form': form, 'role': role, 'is_update': True})

@login_required
def worker_list(request):
    """
    Vista para listar todos los trabajadores
    PostgreSQL: SELECT * FROM projects_worker
    """
    workers = Worker.objects.all()
    return render(request, 'projects/worker_list.html', {'workers': workers})

@login_required
def role_list(request):
    """
    Vista para listar todos los roles
    PostgreSQL: SELECT * FROM projects_role
    """
    roles = Role.objects.all()
    return render(request, 'projects/role_list.html', {'roles': roles})

@login_required
def worker_delete(request, worker_id):
    """
    Vista para eliminar un trabajador
    PostgreSQL: DELETE FROM projects_worker WHERE id = [worker_id]
    """
    worker = get_object_or_404(Worker, id=worker_id)
    if request.method == 'POST':
        worker.delete()
        messages.success(request, f'Trabajador "{worker.name}" eliminado exitosamente!')
        return redirect('projects:worker_list')
    return render(request, 'projects/worker_confirm_delete.html', {'worker': worker})
