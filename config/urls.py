
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path

from memory.registro import (
    FormularioAcceso,
    registrar_usuario
)

urlpatterns = [
    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "accounts/registro/",
        registrar_usuario,
        name="registro"
    ),

    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=FormularioAcceso
        ),
        name="login"
    ),

    path(
        "accounts/",
        include("django.contrib.auth.urls")
    ),

    path(
        "",
        include("memory.urls")
    ),
]
