
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.views.decorators.http import require_http_methods

from memory.registro import (
    FormularioAcceso,
    registrar_usuario
)

acceso = LoginView.as_view(
    template_name="registration/login.html",
    authentication_form=FormularioAcceso,
)

urlpatterns = [
    path("cuentas/registro/", require_http_methods(["GET", "POST"])(registrar_usuario), name="cuentas_registro"),
    path("cuentas/login/", acceso, name="cuentas_login"),
    path("cuentas/logout/", LogoutView.as_view(), name="cuentas_logout"),
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
        acceso,
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
