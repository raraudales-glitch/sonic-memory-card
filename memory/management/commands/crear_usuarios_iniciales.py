import warnings
from getpass import GetPassWarning, getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from memory.models import PerfilJugador


CUENTAS = ("ADMIN", "Stanley", "Nelson", "Astrid", "Rut", "Lester", "Gustavo")
PERMISOS_EDITOR = {"view_personaje", "add_personaje", "change_personaje", "view_partida"}


class Command(BaseCommand):
    help = "Crea las cuentas iniciales y configura sus permisos de administracion."

    def buscar_usuario(self, usuarios, nombre):
        try:
            return usuarios.get(username__iexact=nombre)
        except usuarios.model.DoesNotExist:
            return None
        except usuarios.model.MultipleObjectsReturned as error:
            raise CommandError(f"Hay varias cuentas que coinciden con {nombre}.") from error

    def pedir_clave(self, usuario):
        while True:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", GetPassWarning)
                    clave = getpass(f"Contrasena de {usuario.username}: ")
                    confirmacion = getpass("Confirma la contrasena: ")
            except (GetPassWarning, EOFError, KeyboardInterrupt) as error:
                raise CommandError("Se requiere una terminal interactiva con entrada oculta.") from error

            if clave != confirmacion:
                self.stderr.write("Las contrasenas no coinciden.")
                continue

            try:
                validate_password(clave, usuario)
            except ValidationError as error:
                for mensaje in error.messages:
                    self.stderr.write(mensaje)
                continue

            return clave

    def handle(self, *args, **options):
        Usuario = get_user_model()
        permisos = list(Permission.objects.filter(
            Q(content_type__model="personaje", codename__in=PERMISOS_EDITOR - {"view_partida"})
            | Q(content_type__model="partida", codename="view_partida"),
            content_type__app_label="memory",
        ))
        if {permiso.codename for permiso in permisos} != PERMISOS_EDITOR:
            raise CommandError("Faltan permisos de Django. Ejecuta migrate primero.")

        pendientes = {}
        for nombre in CUENTAS:
            if self.buscar_usuario(Usuario.objects, nombre) is None:
                usuario = Usuario(username=nombre)
                usuario.set_password(self.pedir_clave(usuario))
                pendientes[nombre] = usuario.password

        resumen = []
        with transaction.atomic():
            for nombre in CUENTAS:
                es_admin = nombre == "ADMIN"
                usuario = self.buscar_usuario(Usuario.objects.select_for_update(), nombre)
                creado = False
                if usuario is None:
                    if nombre not in pendientes:
                        raise CommandError(f"La cuenta {nombre} cambio. Ejecuta el comando nuevamente.")
                    usuario, creado = Usuario.objects.select_for_update().get_or_create(
                        username=nombre,
                        defaults={"password": pendientes[nombre]},
                    )

                cambios = []
                for campo, valor in {
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": es_admin,
                }.items():
                    if getattr(usuario, campo) != valor:
                        setattr(usuario, campo, valor)
                        cambios.append(campo)
                if cambios:
                    usuario.save(update_fields=cambios)

                if not es_admin:
                    actuales = set(usuario.user_permissions.values_list("pk", flat=True))
                    if actuales != {permiso.pk for permiso in permisos}:
                        usuario.user_permissions.set(permisos)
                        cambios.append("permisos directos")
                    if usuario.groups.exists():
                        usuario.groups.clear()
                        cambios.append("grupos")

                _, perfil_creado = PerfilJugador.objects.get_or_create(
                    usuario=usuario, defaults={"alias": usuario.username}
                )
                estado = "creado" if creado else "ya existia"
                rol = "superusuario" if es_admin else "STAFF editor"
                detalle = ", ".join(cambios) or "sin cambios de permisos"
                perfil = "perfil creado" if perfil_creado or creado else "perfil conservado"
                resumen.append(f"{usuario.username}: {estado}; {rol}; {detalle}; {perfil}.")

        for linea in resumen:
            self.stdout.write(linea)
