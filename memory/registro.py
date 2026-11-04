
from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.text import slugify

from .models import PerfilJugador


class FormularioRegistro(forms.Form):

    nombre = forms.CharField(
        label="Nombre completo",
        min_length=2,
        max_length=150,
        strip=True
    )

    correo = forms.EmailField(
        label="Correo electrónico",
        max_length=150
    )

    contrasena1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput
    )

    contrasena2 = forms.CharField(
        label="Confirmar contraseña",
        strip=False,
        widget=forms.PasswordInput
    )

    def clean_correo(self):
        correo = self.cleaned_data["correo"].strip().lower()

        Usuario = get_user_model()

        if Usuario.objects.filter(
            email__iexact=correo
        ).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con este correo electrónico."
            )

        return correo

    def clean(self):
        datos = super().clean()

        nombre = datos.get("nombre", "")
        correo = datos.get("correo", "")
        contrasena1 = datos.get("contrasena1")
        contrasena2 = datos.get("contrasena2")

        if contrasena1 and contrasena2:
            if contrasena1 != contrasena2:
                self.add_error(
                    "contrasena2",
                    "Las contraseñas no coinciden."
                )

            else:
                Usuario = get_user_model()

                usuario_temporal = Usuario(
                    username=slugify(nombre)[:35] or "jugador",
                    first_name=nombre,
                    email=correo
                )

                try:
                    validate_password(
                        contrasena1,
                        user=usuario_temporal
                    )

                except ValidationError as error:
                    self.add_error(
                        "contrasena1",
                        error
                    )

        return datos


class FormularioAcceso(AuthenticationForm):

    username = forms.CharField(
        label="Usuario o correo electrónico",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "placeholder": "Usuario o correo electrónico"
            }
        )
    )

    def clean(self):
        identificador = self.cleaned_data.get(
            "username",
            ""
        ).strip()

        if "@" in identificador:
            Usuario = get_user_model()

            usuario = Usuario.objects.filter(
                email__iexact=identificador
            ).first()

            if usuario:
                self.cleaned_data["username"] = (
                    usuario.get_username()
                )

        return super().clean()


def registrar_usuario(request):

    if request.user.is_authenticated:
        return redirect("memory:inicio")

    if request.method == "POST":
        formulario = FormularioRegistro(request.POST)

        if formulario.is_valid():

            nombre = formulario.cleaned_data["nombre"]
            correo = formulario.cleaned_data["correo"]
            contrasena = formulario.cleaned_data["contrasena1"]

            Usuario = get_user_model()

            base = slugify(nombre)[:35].strip("-")

            if not base:
                base = "jugador"

            nombre_usuario = base
            numero = 1

            with transaction.atomic():

                while Usuario.objects.filter(
                    username__iexact=nombre_usuario
                ).exists():

                    numero += 1

                    sufijo = f"-{numero}"

                    nombre_usuario = (
                        base[:35 - len(sufijo)] + sufijo
                    )

                usuario = Usuario.objects.create_user(
                    username=nombre_usuario,
                    email=correo,
                    password=contrasena,
                    first_name=nombre
                )

                PerfilJugador.objects.filter(
                    usuario=usuario
                ).update(
                    alias=nombre[:50]
                )

            login(
                request,
                usuario,
                backend="django.contrib.auth.backends.ModelBackend"
            )

            return redirect("memory:inicio")

    else:
        formulario = FormularioRegistro()

    return render(
        request,
        "registration/registro.html",
        {
            "form": formulario
        }
    )
