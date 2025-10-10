from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path("", views.home_router, name="home"),  # Router post-login
    path("jefe/", views.home_jefe, name="home_jefe"),
    path("constructor/", views.home_constructor, name="home_constructor"),
    path("comercial/", views.home_comercial, name="home_comercial"),
]
