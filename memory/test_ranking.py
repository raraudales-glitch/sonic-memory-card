import hashlib
import json
from datetime import datetime, timedelta, timezone as utc
from io import StringIO
from secrets import token_urlsafe
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.utils.html import escape
from django.urls import reverse

from .models import EnvioRanking, Partida, ResultadoRanking
from .ranking_cliente import RankingNoDisponible, destino_global


ACTUAL = datetime(2026, 11, 23, 6, tzinfo=utc.utc)
PASADA = ACTUAL - timedelta(days=7)
DESTINO = "https://ranking.test"
API = "/api/ranking/"


def credenciales_centrales(usuarios):
    return json.dumps({hashlib.sha256(token.encode()).hexdigest(): usuario for usuario, token in usuarios})


def partida_reportada(puntaje, fin, **campos):
    return {
        "partida_id": str(uuid4()), "dificultad": "FACIL", "puntaje": puntaje,
        "finalizada_en": fin.isoformat(), "estado": "GANADA", "practica": False, **campos,
    }


@override_settings(SECURE_SSL_REDIRECT=False)
class RankingServidorTests(TestCase):
    def setUp(self):
        self.usuarios = {
            nombre: get_user_model().objects.create_user(username=nombre)
            for nombre in ("Ana", "Beto", "Celia", "Dario", "Eva", "Fabio")
        }
        self.client.force_login(self.usuarios["Fabio"])
        reloj = patch("memory.ranking.timezone.now", return_value=ACTUAL + timedelta(days=1))
        reloj.start()
        self.addCleanup(reloj.stop)

    def partida(self, nombre, puntos, fin=ACTUAL, **opciones):
        campos = {
            "estado": Partida.Estado.GANADA, "practica": False, "dificultad": "FACIL",
            "limite_segundos": 150, "fin_servidor": fin,
        }
        return Partida.objects.create(usuario=self.usuarios[nombre], puntaje=puntos, **(campos | opciones))

    @override_settings(RANKING_URL=DESTINO)
    def test_top_compartido_usa_solamente_las_partidas_oficiales_de_postgresql(self):
        for nombre, puntos in (("Ana", 900), ("Ana", 700), ("Beto", 1500), ("Celia", 1400),
                               ("Dario", 1300), ("Eva", 1200), ("Fabio", 1100)):
            self.partida(nombre, puntos)
        self.partida("Fabio", 0, practica=True)
        self.partida("Fabio", 1700, estado=Partida.Estado.PERDIDA)
        self.partida("Fabio", 1700, estado=Partida.Estado.ABANDONADA)
        self.partida("Fabio", 1750, fin=ACTUAL - timedelta(microseconds=1))
        ResultadoRanking.objects.create(
            partida_id=uuid4(), jugador="Remoto", dificultad="FACIL", puntaje=1750, finalizada_en=ACTUAL,
        )

        url = reverse("memory:top_semanal")
        segundo = Client()
        segundo.force_login(self.usuarios["Ana"])
        with patch("memory.ranking.consultar_global") as consultar_remoto:
            respuesta = self.client.get(url)
            de_ana = segundo.get(url)
            anterior = self.client.get(url, {"semana": "2026-11-16"})
        consultar_remoto.assert_not_called()

        ranking = respuesta.context["ranking"]
        self.assertEqual(ranking["inicio"], "2026-11-23")
        self.assertEqual(ranking["posicion"], 6)
        self.assertEqual(
            [(fila["jugador"], fila["puntos"]) for fila in ranking["mejores"]],
            [("Ana", 1600), ("Beto", 1500), ("Celia", 1400), ("Dario", 1300), ("Eva", 1200)],
        )
        self.assertEqual(ranking["mejores"][0]["victorias"], 2)
        self.assertEqual(de_ana.context["ranking"]["mejores"], ranking["mejores"])
        self.assertEqual(de_ana.context["ranking"]["posicion"], 1)
        self.assertEqual(anterior.context["ranking"]["mejores"][0]["puntos"], 1750)
        for medalla in ("🥇", "🥈", "🥉"):
            self.assertContains(respuesta, medalla)
        self.assertContains(respuesta, "Tu posición es #6")
        self.assertNotContains(respuesta, "Remoto")

    def test_boton_en_menu_y_en_partidas_oficiales_y_de_practica(self):
        destino = escape(reverse("memory:top_semanal"))
        perfil = escape(reverse("memory:perfil"))
        menu = self.client.get(reverse("memory:inicio"))
        self.assertContains(menu, "🏆 TOP 5")
        self.assertContains(menu, f'href="{destino}"')
        self.assertContains(menu, f'href="{perfil}"')
        for practica in (False, True):
            for dificultad in ("FACIL", "NORMAL", "DIFICIL"):
                with self.subTest(practica=practica, dificultad=dificultad):
                    partida = self.partida(
                        "Fabio", 0, practica=practica, dificultad=dificultad,
                        estado=Partida.Estado.EN_CURSO, fin_servidor=None,
                    )
                    url = reverse("memory:jugar_partida", args=[partida.pk])
                    respuesta = self.client.get(url)
                    self.assertContains(respuesta, f'href="{destino}" target="_blank" rel="noopener"')
                    self.assertContains(respuesta, f'href="{perfil}" target="_blank" rel="noopener"')
                    self.assertContains(respuesta, "🏆 TOP 5")
                    self.assertContains(respuesta, "memory/js/menu_opciones.js")
                    Partida.objects.filter(pk=partida.pk).update(estado=Partida.Estado.ABANDONADA)

    def test_top_requiere_sesion(self):
        respuesta = Client().get(reverse("memory:top_semanal"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.url.startswith(reverse("login")))


@override_settings(
    SECURE_SSL_REDIRECT=False,
    RANKING_CENTRAL=False,
    RANKING_URL="",
    RANKING_CREDENCIALES_LOCALES="{}",
    RANKING_CREDENCIALES_CENTRALES="{}",
)
class RankingGlobalTests(TestCase):
    def setUp(self):
        self.token = token_urlsafe(32)
        self.segundo_token = token_urlsafe(32)
        self.central = Client(enforce_csrf_checks=True)

    def enviar(self, datos, token, *, secure=True):
        return self.central.post(
            API + "resultados/", datos, content_type="application/json", secure=secure,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    def consultar(self, token=None, semana=None):
        cabeceras = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        consulta = {"semana": semana} if semana else {}
        return self.central.get(API + "semanal/", consulta, secure=True, **cabeceras)

    def test_top_cinco_acumulado_desempates_posicion_e_historial(self):
        jugadores = {nombre: token_urlsafe(32) for nombre in ("Ana", "Beto", "Celia", "Dario", "Eva", "Fabio")}
        with override_settings(
            RANKING_CENTRAL=True, ROOT_URLCONF="config.ranking_urls",
            RANKING_CREDENCIALES_CENTRALES=credenciales_centrales(jugadores.items()),
        ), patch("memory.ranking.timezone.now", return_value=ACTUAL + timedelta(days=1)):
            resultados = [
                ("Ana", 900, 2), ("Ana", 100, 3), ("Beto", 1000, 1),
                ("Celia", 500, 0), ("Celia", 500, 1), ("Dario", 800, 3),
                ("Eva", 700, 1), ("Fabio", 600, 1),
            ]
            for nombre, puntos, minutos in resultados:
                datos = partida_reportada(puntos, ACTUAL + timedelta(minutes=minutos))
                self.assertEqual(self.enviar(datos, jugadores[nombre]).status_code, 201)
            domingo = partida_reportada(1750, ACTUAL - timedelta(microseconds=1))
            self.assertEqual(self.enviar(domingo, jugadores["Fabio"]).status_code, 201)
            respuesta = self.consultar(jugadores["Fabio"]).json()
            self.assertEqual(respuesta["inicio"], "2026-11-23")
            self.assertEqual(respuesta["fin"], "2026-11-29")
            self.assertEqual(respuesta["posicion"], 6)
            self.assertEqual(respuesta["anteriores"], ["2026-11-16"])
            self.assertEqual(
                [(f["jugador"], f["puntos"], f["victorias"]) for f in respuesta["mejores"]],
                [("Celia", 1000, 2), ("Ana", 1000, 2), ("Beto", 1000, 1), ("Dario", 800, 1), ("Eva", 700, 1)],
            )
            pasada = self.consultar(jugadores["Fabio"], "2026-11-16").json()
            self.assertEqual(pasada["posicion"], 1)
            self.assertEqual(pasada["mejores"][0]["puntos"], 1750)
            self.assertEqual(self.consultar(semana="2026-11-22").status_code, 400)

        with override_settings(RANKING_CENTRAL=True, ROOT_URLCONF="config.ranking_urls"):
            with patch("memory.ranking.timezone.now", return_value=ACTUAL + timedelta(days=7)):
                nueva = self.consultar().json()
            self.assertEqual(nueva["inicio"], "2026-11-30")
            self.assertEqual(nueva["mejores"], [])
            self.assertEqual(nueva["anteriores"], ["2026-11-23", "2026-11-16"])

    def test_ingreso_https_autorizado_idempotente_y_solo_victorias(self):
        claves = credenciales_centrales([("Ana", self.token), ("Ana", self.segundo_token)])
        with override_settings(
            RANKING_CENTRAL=True, ROOT_URLCONF="config.ranking_urls", RANKING_CREDENCIALES_CENTRALES=claves,
        ), patch("memory.ranking.timezone.now", return_value=ACTUAL):
            datos = partida_reportada(900, PASADA)
            with override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[]):
                respuesta_http = Client().post(API + "resultados/", datos, content_type="application/json")
                self.assertEqual(respuesta_http.status_code, 301)
            self.assertEqual(self.enviar(datos, self.token, secure=False).status_code, 403)
            self.assertEqual(self.enviar(datos, token_urlsafe(32)).status_code, 401)
            self.assertEqual(self.enviar(datos, self.token).status_code, 201)
            self.assertEqual(self.enviar(datos, self.segundo_token).status_code, 200)
            self.assertEqual(self.enviar({**datos, "puntaje": 901}, self.token).status_code, 409)
            for campos in (
                {"practica": True}, {"estado": "PERDIDA"}, {"estado": "ABANDONADA"},
                {"estado": "TIEMPO_AGOTADO"}, {"puntaje": True}, {"puntaje": 10000}, {"jugador": "Otro"},
            ):
                invalida = {**partida_reportada(900, PASADA), **campos}
                self.assertEqual(self.enviar(invalida, self.token).status_code, 400)
            self.assertEqual(ResultadoRanking.objects.count(), 1)

    def test_instalaciones_comparten_resultados_y_vinculan_copias_de_una_cuenta(self):
        usuarios = get_user_model()
        local_a = usuarios.objects.create_user(username="Stanley")
        local_b = usuarios.objects.create_user(username="stanley-copia")
        Partida.objects.create(usuario=local_a, dificultad="FACIL", limite_segundos=150,
                               estado=Partida.Estado.GANADA, puntaje=1000, fin_servidor=ACTUAL)
        Partida.objects.create(usuario=local_b, dificultad="FACIL", limite_segundos=150,
                               estado=Partida.Estado.GANADA, puntaje=800, fin_servidor=ACTUAL)
        claves = credenciales_centrales([("Stanley", self.token), ("Stanley", self.segundo_token)])
        top = reverse("memory:top_sincronizado")

        def transporte(destino, recurso, *, token=None, datos=None):
            self.assertEqual(destino, DESTINO)
            with override_settings(
                RANKING_CENTRAL=True, ROOT_URLCONF="config.ranking_urls", RANKING_CREDENCIALES_CENTRALES=claves,
            ):
                if datos is not None:
                    respuesta = self.enviar(datos, token)
                else:
                    respuesta = self.central.get(
                        API + recurso, secure=True, HTTP_AUTHORIZATION=f"Bearer {token}",
                    )
                self.assertIn(respuesta.status_code, (200, 201))
                return respuesta.json()

        with override_settings(RANKING_URL=DESTINO), patch(
            "memory.ranking.timezone.now", return_value=ACTUAL + timedelta(days=1)
        ), patch("memory.ranking_cliente.peticion_global", side_effect=transporte):
            resultados = []
            for usuario, token in ((local_a, self.token), (local_b, self.segundo_token)):
                with override_settings(RANKING_CREDENCIALES_LOCALES=json.dumps({usuario.username: token})):
                    call_command("sincronizar_ranking", stdout=StringIO())
            for usuario, token in ((local_a, self.token), (local_b, self.segundo_token)):
                self.client.force_login(usuario)
                with override_settings(RANKING_CREDENCIALES_LOCALES=json.dumps({usuario.username: token})):
                    respuesta = self.client.get(top)
                self.assertContains(respuesta, "Tu posición es #1")
                self.assertContains(respuesta, "🥇")
                resultados.append(respuesta.context["ranking"]["mejores"])
        self.assertEqual(EnvioRanking.objects.count(), 2)
        self.assertEqual(resultados[0], resultados[1])
        self.assertEqual(resultados[0], [{"jugador": "Stanley", "puntos": 1800, "victorias": 2}])

    def test_fallo_de_red_avisa_y_reintenta_solo_victorias_oficiales(self):
        usuario = get_user_model().objects.create_user(username="Nelson")
        oficial = Partida.objects.create(usuario=usuario, dificultad="FACIL", limite_segundos=150,
                                        estado=Partida.Estado.GANADA, puntaje=1550, fin_servidor=ACTUAL)
        for estado, practica in (("GANADA", True), ("PERDIDA", False), ("ABANDONADA", False)):
            Partida.objects.create(usuario=usuario, dificultad="FACIL", limite_segundos=150,
                                   estado=estado, practica=practica, fin_servidor=ACTUAL)
        self.client.force_login(usuario)
        with override_settings(RANKING_URL=DESTINO, RANKING_CREDENCIALES_LOCALES=json.dumps({"Nelson": self.token})):
            with patch("memory.ranking_cliente.peticion_global", side_effect=RankingNoDisponible):
                call_command("sincronizar_ranking", stdout=StringIO())
                self.assertFalse(EnvioRanking.objects.exists())
                respuesta = self.client.get(reverse("memory:top_sincronizado"))
                self.assertContains(respuesta, "El ranking global no está disponible")
                self.assertNotContains(respuesta, "1550")
                self.assertContains(self.client.get(reverse("memory:inicio")), "🏆 TOP 5")
            with patch("memory.ranking_cliente.peticion_global", return_value={"ok": True}) as peticion:
                call_command("sincronizar_ranking", stdout=StringIO())
                call_command("sincronizar_ranking", stdout=StringIO())
                peticion.assert_called_once()
                self.assertEqual(peticion.call_args.kwargs["datos"]["partida_id"], str(oficial.pk))
                self.assertEqual(EnvioRanking.objects.get().partida, oficial)

    def test_cliente_rechaza_destinos_sin_https(self):
        for direccion in ("", "http://ranking.test"):
            with self.subTest(direccion=direccion), override_settings(RANKING_URL=direccion):
                with self.assertRaises(RankingNoDisponible):
                    destino_global()
