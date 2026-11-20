from io import StringIO
from secrets import token_urlsafe
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from memory.management.commands import crear_usuarios_iniciales
from memory.models import Partida, PerfilJugador, Personaje


class UsuariosInicialesTests(TestCase):
    nombres = ("ADMIN", "Stanley", "Nelson", "Astrid", "Rut", "Lester", "Gustavo")
    permisos_editor = {
        "memory.view_personaje", "memory.add_personaje", "memory.change_personaje",
        "memory.view_partida",
    }

    def ejecutar(self, faltantes):
        claves = {nombre: token_urlsafe(25) for nombre in faltantes}
        entradas = [clave for nombre in faltantes for clave in [claves[nombre]] * 2]
        salida = StringIO()
        with patch.object(crear_usuarios_iniciales, "getpass", side_effect=entradas) as pedir:
            call_command("crear_usuarios_iniciales", stdout=salida)
        self.assertEqual(pedir.call_count, len(entradas))
        for clave in claves.values():
            self.assertNotIn(clave, salida.getvalue())
        return claves, salida.getvalue()

    def test_crea_cuentas_perfiles_y_permisos(self):
        claves, salida = self.ejecutar(self.nombres)
        Usuario = get_user_model()
        self.assertEqual(set(Usuario.objects.values_list("username", flat=True)), set(self.nombres))
        for nombre in self.nombres:
            with self.subTest(usuario=nombre):
                usuario = Usuario.objects.get(username=nombre)
                self.assertTrue(usuario.is_active)
                self.assertTrue(usuario.is_staff)
                self.assertEqual(usuario.is_superuser, nombre == "ADMIN")
                self.assertTrue(usuario.check_password(claves[nombre]))
                self.assertTrue(PerfilJugador.objects.filter(usuario=usuario).exists())
                self.assertIn(f"{nombre}: creado", salida)
                if nombre == "ADMIN":
                    self.assertTrue(usuario.has_perm("auth.delete_user"))
                    self.assertTrue(usuario.has_perm("auth.change_group"))
                else:
                    self.assertEqual(usuario.get_all_permissions(), self.permisos_editor)

    def test_conserva_datos_y_contrasenas_al_repetir(self):
        Usuario = get_user_model()
        usuario = Usuario.objects.create_user(
            username="stanley", password=token_urlsafe(25), email="stanley@example.test",
            is_active=False, is_superuser=True,
        )
        clave_original = usuario.password
        usuario.perfil.alias = "Alias previo"
        usuario.perfil.save(update_fields=["alias"])
        partida = Partida.objects.create(
            usuario=usuario, dificultad="FACIL", limite_segundos=150, puntaje=125,
            estado=Partida.Estado.GANADA,
        )
        gustavo = Usuario.objects.create_user(username="Gustavo", password=token_urlsafe(25))
        gustavo.perfil.delete()
        tercero = Usuario.objects.create_user(username="otro")
        grupo = Group.objects.create(name="Grupo anterior")
        permiso = Permission.objects.get(content_type__app_label="auth", codename="change_user")
        grupo.permissions.add(permiso)
        usuario.groups.add(grupo)
        usuario.user_permissions.add(permiso)
        tercero.groups.add(grupo)

        self.ejecutar([n for n in self.nombres if n not in ("Stanley", "Gustavo")])
        _, salida = self.ejecutar([])
        self.assertEqual(Usuario.objects.count(), 8)
        self.assertEqual(salida.count("ya existia"), 7)
        usuario.refresh_from_db()
        self.assertEqual(usuario.password, clave_original)
        self.assertEqual(usuario.email, "stanley@example.test")
        self.assertEqual(usuario.perfil.alias, "Alias previo")
        self.assertTrue(usuario.is_active and usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(usuario.get_all_permissions(), self.permisos_editor)
        self.assertTrue(tercero.has_perm("auth.change_user"))
        self.assertEqual(Partida.objects.get(pk=partida.pk).puntaje, 125)
        self.assertTrue(PerfilJugador.objects.filter(usuario=gustavo).exists())

    def test_acceso_y_restricciones_en_el_panel(self):
        claves, _ = self.ejecutar(self.nombres)
        Usuario = get_user_model()
        editor = Usuario.objects.get(username="Stanley")
        personaje = Personaje.objects.create(
            clave="sonic", nombre="Sonic", origen=Personaje.Origen.VIDEOJUEGO,
        )
        partida = Partida.objects.create(usuario=editor, dificultad="FACIL", limite_segundos=150)
        url = reverse("admin:login")
        for nombre in self.nombres:
            with self.subTest(usuario=nombre):
                self.client.logout()
                respuesta = self.client.post(url, {"username": nombre, "password": claves[nombre]})
                self.assertEqual(respuesta.status_code, 302)
                self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
                for ruta in ("admin:auth_user_changelist", "admin:auth_group_changelist"):
                    esperado = 200 if nombre == "ADMIN" else 403
                    self.assertEqual(self.client.get(reverse(ruta)).status_code, esperado)

        editar = reverse("admin:memory_personaje_change", args=[personaje.pk])
        datos = {"clave": "sonic", "nombre": "Sonic editado", "origen": personaje.origen,
                 "descripcion": "Descripcion", "_save": "Guardar"}
        self.assertEqual(self.client.get(reverse("admin:memory_personaje_add")).status_code, 200)
        self.assertEqual(self.client.post(editar, datos).status_code, 302)
        personaje.refresh_from_db()
        self.assertFalse(personaje.activo)
        self.assertEqual(personaje.nombre, "Sonic editado")
        detalle = reverse("admin:memory_partida_change", args=[partida.pk])
        respuesta = self.client.get(detalle)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, "field-estado_juego")
        self.assertNotContains(respuesta, "field-semilla")
        self.assertEqual(self.client.post(detalle, {"puntaje": 50}).status_code, 403)
        for ruta, args in (
            ("admin:auth_user_add", []),
            ("admin:auth_user_delete", [editor.pk]),
            ("admin:auth_user_password_change", [editor.pk]),
            ("admin:memory_personaje_delete", [personaje.pk]),
            ("admin:memory_partida_delete", [partida.pk]),
            ("admin:memory_perfiljugador_changelist", []),
        ):
            self.assertEqual(self.client.get(reverse(ruta, args=args)).status_code, 403)
