# catalog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("materiales/", views.material_list, name="material_list"),
    path("materiales/nuevo/", views.material_create, name="material_create"),
    path("materiales/<int:pk>/editar/", views.material_update, name="material_update"),
    path("materiales/<int:pk>/eliminar/", views.material_delete, name="material_delete"),

    # gestión de proveedores por material
    path("materiales/<int:material_id>/proveedores/", views.material_suppliers_list, name="material_suppliers_list"),
    path("materiales/<int:material_id>/proveedores/nuevo/", views.material_supplier_create, name="material_supplier_create"),
    path("materiales/<int:material_id>/proveedores/<int:link_id>/editar/", views.material_supplier_update, name="material_supplier_update"),
    path("materiales/<int:material_id>/proveedores/<int:link_id>/preferido/", views.material_supplier_set_preferred, name="material_supplier_set_preferred"),
    path("materiales/<int:material_id>/proveedores/<int:link_id>/eliminar/", views.material_supplier_delete, name="material_supplier_delete"),
]
