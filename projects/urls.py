from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/update/', views.project_update, name='project_update'),
    path('<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('<int:project_id>/update-status/', views.update_project_status, name='update_project_status'),
    path('view/', views.project_view, name='project_view'),
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

]
