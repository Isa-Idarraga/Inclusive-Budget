from django.urls import path
from . import views

app_name = "manual"

urlpatterns = [
    path("", views.manual_usuario, name="manual"),
]


