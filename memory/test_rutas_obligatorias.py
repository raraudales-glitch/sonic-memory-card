from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError, connection
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Movimiento, Partida
from .test_auditoria_partidas import crear, preparar, ruta


class RutasObligatoriasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = preparar()
        cls.otro = get_user_model().objects.create_user(username="otro")

    def partida_final(self, usuario=None, **campos):
        valores = {
            "usuario": usuario or self.usuario,
            "dificultad": Partida.Dificultad.FACIL,
            "estado": Partida.Estado.GANADA,
            "limite_segundos": 150,
            "fin_servidor": timezone.now(),
            "duracion_segundos": 50,
            "puntaje": 1000,
        }
        return Partida.objects.create(**(valores | campos))

    def test_clasificacion_publica_con_mejor_victoria_y_desempates(self):
        fecha = timezone.now() - timedelta(days=40)
        self.partida_final(puntaje=1001, duracion_segundos=45, fin_servidor=fecha)
        self.partida_final(puntaje=1002, duracion_segundos=45, fin_servidor=fecha)
        self.partida_final(puntaje=1002, duracion_segundos=40, fin_servidor=fecha + timedelta(days=1))
        mejor = self.partida_final(puntaje=1002, duracion_segundos=40, fin_servidor=fecha)
        segundo = self.partida_final(self.otro, puntaje=1002, duracion_segundos=40,
                                     fin_servidor=fecha + timedelta(days=1))
        self.partida_final(self.otro, estado=Partida.Estado.PERDIDA, puntaje=9999)
        self.partida_final(self.otro, practica=True, puntaje=0)
        normal = self.partida_final(self.otro, dificultad=Partida.Dificultad.NORMAL)
        dificil = self.partida_final(dificultad=Partida.Dificultad.DIFICIL)
        for nivel, partidas in (("facil", [mejor, segundo]), ("normal", [normal]), ("dificil", [dificil])):
            with self.subTest(nivel=nivel):
                respuesta = self.client.get("/clasificacion/", {"nivel": nivel})
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(list(respuesta.context["partidas"]), partidas)
        self.assertEqual(self.client.get("/clasificacion/?nivel=inexistente").status_code, 400)

    def test_clasificacion_limita_a_diez_despues_de_agrupar(self):
        usuarios = [get_user_model().objects.create_user(username=f"jugador{i}") for i in range(12)]
        partidas = [
            self.partida_final(usuario, puntaje=2000 - i) for i, usuario in enumerate(usuarios)
        ]
        for puntaje in range(10):
            self.partida_final(usuarios[0], puntaje=1900 + puntaje)
        respuesta = self.client.get("/clasificacion/")
        self.assertEqual(list(respuesta.context["partidas"]), partidas[:10])

    def test_salud_responde_con_la_base_disponible(self):
        respuesta = self.client.get("/salud/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"ok": True})
        self.assertIn("no-store", respuesta.headers["Cache-Control"])

    def test_salud_oculta_el_error_de_conexion(self):
        with patch.object(connection, "cursor", side_effect=OperationalError("detalle privado")):
            respuesta = self.client.get("/salud/")
        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(respuesta.json(), {"ok": False})
        self.assertNotContains(respuesta, "detalle privado", status_code=503)

    def test_historial_paginado_y_privado(self):
        fecha = timezone.now() - timedelta(seconds=11)
        propias = []
        for segundo in range(11):
            with patch("django.utils.timezone.now", return_value=fecha + timedelta(seconds=segundo)):
                propias.append(self.partida_final())
        self.partida_final(self.otro)
        self.assertEqual(self.client.get("/historial/").status_code, 302)
        self.client.force_login(self.usuario)
        primera = self.client.get("/historial/")
        self.assertEqual(list(primera.context["pagina"]), propias[:0:-1])
        self.assertContains(primera, "?pagina=2")
        segunda = self.client.get("/historial/?pagina=2")
        self.assertEqual(list(segunda.context["pagina"]), propias[:1])

    def test_resultado_final_y_seleccion_de_dificultad(self):
        ganada = self.partida_final()
        ajena = self.partida_final(self.otro)
        self.assertContains(self.client.get("/instrucciones/"), "Fallos permitidos")
        self.assertEqual(self.client.get("/jugar/").status_code, 302)
        self.assertEqual(self.client.get(ruta("resultado", ganada)).status_code, 302)
        self.client.force_login(self.usuario)
        activa = crear(self.client)
        self.assertContains(self.client.get("/jugar/"), "DIFICIL")
        self.assertTrue(self.client.get("/jugar/?practica=1").context["practica"])
        self.assertRedirects(self.client.get(ruta("resultado", activa)), ruta("jugar_partida", activa))
        self.assertContains(self.client.get(ruta("resultado", ganada)), "Ganada")
        self.assertContains(self.client.get(ruta("resultado", ganada)), "1000")
        self.assertEqual(self.client.get(ruta("resultado", ajena)).status_code, 404)

    def test_api_propiedad_metodos_y_estado_sin_tablero_oculto(self):
        self.client.force_login(self.usuario)
        partida = crear(self.client)
        estado = ruta("estado_api", partida)
        accion = ruta("accion_api", partida)
        abandono = ruta("abandonar_api", partida)
        self.assertEqual(Client().get(estado).status_code, 302)
        respuesta = self.client.get(estado)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["ultima_secuencia"], 0)
        self.assertNotIn("orden", respuesta.json())
        self.assertNotIn("semilla", respuesta.json())
        self.assertEqual(self.client.post(estado).status_code, 405)
        self.assertEqual(self.client.get(accion).status_code, 405)
        self.assertEqual(self.client.get(abandono).status_code, 405)
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(estado).status_code, 404)
        self.assertEqual(self.client.post(accion, {"posicion": 0, "seq_num": 1},
                                          content_type="application/json").status_code, 404)
        self.assertEqual(self.client.post(abandono).status_code, 404)

    def test_api_accion_csrf_secuencia_idempotencia_y_abandono(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.client.force_login(self.usuario)
        partida = crear(self.client)
        cliente.get(ruta("jugar_partida", partida))
        token = cliente.cookies["csrftoken"].value
        accion = ruta("accion_api", partida)
        abandono = ruta("abandonar_api", partida)

        def enviar(posicion, secuencia, **cabeceras):
            return cliente.post(accion, {"posicion": posicion, "seq_num": secuencia},
                                content_type="application/json", **cabeceras)

        self.assertEqual(enviar(0, 1).status_code, 403)
        self.assertEqual(cliente.post(abandono).status_code, 403)
        csrf = {"HTTP_X_CSRFTOKEN": token}
        self.assertEqual(enviar(True, 1, **csrf).status_code, 400)
        self.assertEqual(enviar(0, 2, **csrf).status_code, 409)
        aceptada = enviar(0, 1, **csrf)
        self.assertEqual(aceptada.status_code, 200)
        self.assertEqual(enviar(0, 1, **csrf).json(), aceptada.json())
        self.assertEqual(enviar(1, 1, **csrf).status_code, 409)
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 1)
        respuesta = cliente.post(abandono, **csrf)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["estado"], Partida.Estado.ABANDONADA)

    def test_api_rechaza_jugada_despues_del_tiempo_oficial(self):
        self.client.force_login(self.usuario)
        partida = crear(self.client)
        Partida.objects.filter(pk=partida.pk).update(inicio_servidor=timezone.now() - timedelta(minutes=5))
        estado = self.client.get(ruta("estado_api", partida)).json()
        self.assertEqual(estado["tiempo_restante"], 0)
        self.assertEqual(estado["estado"], Partida.Estado.TIEMPO_AGOTADO)
        respuesta = self.client.post(ruta("accion_api", partida), {"posicion": 0, "seq_num": 1},
                                     content_type="application/json")
        self.assertEqual(respuesta.status_code, 409)
        partida.refresh_from_db()
        self.assertEqual(partida.estado, Partida.Estado.TIEMPO_AGOTADO)
        self.assertEqual(partida.movimientos, 0)

    def test_rutas_de_cuentas_reutilizan_los_formularios_y_cierre(self):
        registro = self.client.get("/cuentas/registro/")
        self.assertTemplateUsed(registro, "registration/registro.html")
        self.assertTemplateUsed(self.client.get("/cuentas/login/"), "registration/login.html")
        contrasena = "W9kz%8qV4!fP7"
        correo = "jugadora@example.test"
        respuesta = self.client.post("/cuentas/registro/", {
            "nombre": "Jugadora Nueva",
            "correo": correo,
            "contrasena1": contrasena,
            "contrasena2": contrasena,
        })
        self.assertEqual(respuesta.status_code, 302)
        registrada = get_user_model().objects.get(email=correo)
        self.assertEqual(self.client.get("/cuentas/logout/").status_code, 405)
        self.assertEqual(self.client.post("/cuentas/logout/").status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        acceso = self.client.post("/cuentas/login/", {"username": correo, "password": contrasena})
        self.assertEqual(acceso.status_code, 302)
        self.assertEqual(self.client.session["_auth_user_id"], str(registrada.pk))
