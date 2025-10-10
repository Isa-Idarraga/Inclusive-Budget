from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("create/", views.project_create, name="project_create"),
    path("<int:project_id>/", views.project_detail, name="project_detail"),
    path("<int:project_id>/update/", views.project_update, name="project_update"),
    path("<int:project_id>/delete/", views.project_delete, name="project_delete"),
    path(
        "<int:project_id>/update-status/",
        views.update_project_status,
        name="update_project_status",
    ),
    path(
        "<int:project_id>/recalculate-fields/",
        views.recalculate_legacy_fields,
        name="recalculate_legacy_fields",
    ),
    path("view/", views.project_view, name="project_view"),
    # Nuevas URLs para trabajadores y roles
    path('workers/create/', views.worker_create, name='worker_create'),
    path('workers/', views.worker_list, name='worker_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/', views.role_list, name='role_list'),
    path('roles/<int:role_id>/update/', views.role_update, name='role_update'),
    path('workers/<int:worker_id>/delete/', views.worker_delete, name='worker_delete'),
    path('<int:project_id>/tablero/', views.project_board, name='project_board'),
    path('roles/<int:role_id>/delete/', views.role_delete, name='role_delete'),
    path("proyectos/<int:project_id>/registrar_entrada_material/", views.registrar_entrada_material, name="registrar_entrada_material"),
    path('entrada/<int:entrada_id>/editar/', views.editar_entrada_material, name='editar_entrada_material'),
    path('entrada/<int:entrada_id>/borrar/', views.borrar_entrada_material, name='borrar_entrada_material'),

    # URLs para consumo diario de materiales (RF17A)
    path('<int:project_id>/consumo/registrar/', views.registrar_consumo_material, name='registrar_consumo_material'),
    path('<int:project_id>/consumo/listar/', views.listar_consumos_proyecto, name='listar_consumos_proyecto'),
    
    # URLs para presupuesto detallado
    path('detailed/create/', views.detailed_project_create, name='detailed_project_create'),
    path('<int:project_id>/detailed-budget/edit/', views.detailed_budget_edit, name='detailed_budget_edit'),
    path('<int:project_id>/detailed-budget/view/', views.detailed_budget_view, name='detailed_budget_view'),
    
    # URLs para gestión de precios (solo JEFE)
    path('budget/management/', views.budget_management, name='budget_management'),
    path('budget/item/<int:item_id>/update/', views.budget_item_update, name='budget_item_update'),
    
    # URLs para gestión de ítems del presupuesto
    path('budget/items/', views.budget_items_list, name='budget_items_list'),
    path('budget/items/create/', views.budget_item_create, name='budget_item_create'),
    path('budget/items/<int:item_id>/edit/', views.budget_item_edit, name='budget_item_edit'),
    path('budget/items/<int:item_id>/delete/', views.budget_item_delete, name='budget_item_delete'),
    path('budget/items/<int:item_id>/toggle/', views.budget_item_toggle, name='budget_item_toggle'),
    path('<int:project_id>/consumo/api/fecha/', views.obtener_consumos_fecha, name='obtener_consumos_fecha'),
    path('<int:project_id>/consumo/api/mes/', views.obtener_consumos_mes, name='obtener_consumos_mes'),  # RF17C
    path('consumo/<int:consumo_id>/editar/', views.editar_consumo_material, name='editar_consumo_material'),
    path('consumo/<int:consumo_id>/eliminar/', views.eliminar_consumo_material, name='eliminar_consumo_material'),
]
