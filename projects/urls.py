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
    path('<int:project_id>/tablero/', views.project_board, name='project_board'),
]
