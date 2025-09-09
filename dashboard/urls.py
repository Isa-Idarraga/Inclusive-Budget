from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_router, name="home"),  # ← este es el router post-login
    path("jefe/", views.home_jefe, name="home_jefe"),
    path("gestor/", views.home_gestor, name="home_gestor"),
]
