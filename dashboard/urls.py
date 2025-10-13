from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path("", views.home_router, name="home"),  # Router post-login
    path("jefe/", views.home_jefe, name="home_jefe"),
    path("jefe/kpis/", views.kpis, name="kpis"),
    path("jefe/kpis/data/", views.kpis_data, name="kpis_data"),
    path("constructor/", views.home_constructor, name="home_constructor"),
    path("comercial/", views.home_comercial, name="home_comercial"),
]
