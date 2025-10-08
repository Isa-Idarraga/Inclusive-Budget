# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),

    # Gestión de usuarios (Solo JEFE)
    path("manage/", views.user_list, name="user_list"),
    path("manage/create/", views.user_create, name="user_create"),
    path("manage/<int:user_id>/edit/", views.user_update, name="user_update"),
    path("manage/<int:user_id>/delete/", views.user_delete, name="user_delete"),
]
