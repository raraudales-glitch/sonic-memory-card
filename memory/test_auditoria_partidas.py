from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Movimiento, Partida, PerfilJugador, Personaje
from .services import NIVELES, PERSONAJES_POR_NIVEL


def preparar():
    Personaje.objects.bulk_create([
        Personaje(clave=clave, nombre=clave, origen=Personaje.Origen.VIDEOJUEGO,
                  imagen=f"auditoria/{clave}.png")
        for clave in PERSONAJES_POR_NIVEL["DIFICIL"]
    ])
    return get_user_model().objects.create_user(username="auditoria")


def crear(cliente, dificultad="FACIL", **datos):
    respuesta = cliente.post(reverse("memory:nueva_partida"),
                             {"dificultad": dificultad, **datos},
                             content_type="application/json", secure=True)
    return Partida.objects.get(pk=respuesta.json()["partida"]["id"])


def ruta(nombre, partida, *args):
    return reverse(f"memory:{nombre}", args=[partida.pk, *args])


def girar(cliente, partida, posicion, secuencia, **datos):
    return cliente.post(ruta("voltear", partida),
                        {"posicion": posicion, "seq_num": secuencia, **datos},
                        content_type="application/json")


def orden_por_parejas(partida):
    orden = partida.estado_juego["orden"]
    return sorted(range(len(orden)), key=orden.__getitem__)


@override_settings(SECURE_SSL_REDIRECT=False)
class AuditoriaPartidasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = preparar()
        cls.otro = get_user_model().objects.create_user(username="otro")

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_tablero_oculto_y_primer_volteo(self):
        partida = crear(self.client, "DIFICIL")
        orden = partida.estado_juego["orden"]
        self.assertEqual(Counter(orden), dict.fromkeys(PERSONAJES_POR_NIVEL["DIFICIL"], 2))
        pagina = self.client.get(ruta("jugar_partida", partida))
        self.assertNotContains(pagina, "auditoria/")
        self.assertContains(pagina, 'class="carta"', count=36)
        estado = self.client.get(ruta("estado_partida", partida)).json()
        self.assertNotIn("orden", estado)
        self.assertNotIn("semilla", estado)
        self.assertEqual((estado["visibles"], estado["emparejadas"]), ([], []))
        self.assertFalse(self.client.post(ruta("vista_previa", partida)).json()["activa"])
        self.assertEqual(self.client.get(ruta("carta_vista_previa", partida, 0)).status_code, 403)
        respuesta = girar(self.client, partida, 0, 1).json()
        self.assertEqual(respuesta["carta"]["clave"], orden[0])
        estado = self.client.get(ruta("estado_partida", partida)).json()
        self.assertEqual([c["posicion"] for c in estado["visibles"]], [0])

    def test_vista_previa_solo_en_su_ventana(self):
        for dificultad in ("FACIL", "NORMAL"):
            with self.subTest(dificultad=dificultad):
                partida = crear(self.client, dificultad)
                carta = ruta("carta_vista_previa", partida, 0)
                self.assertEqual(self.client.get(carta).status_code, 403)
                inicio = ruta("vista_previa", partida)
                self.assertEqual(self.client.get(inicio).status_code, 405)
                partida.refresh_from_db()
                self.assertNotIn("vista_previa_inicio", partida.estado_juego)
                ahora = timezone.now()
                with patch("memory.services.timezone.now", return_value=ahora):
                    self.assertTrue(self.client.post(inicio).json()["activa"])
                    self.assertEqual(self.client.get(carta).status_code, 200)
                    self.assertEqual(girar(self.client, partida, 0, 1).status_code, 409)
                luego = ahora + timedelta(seconds=NIVELES[dificultad]["vista_previa"] + 1)
                with patch("memory.services.timezone.now", return_value=luego):
                    self.assertFalse(self.client.post(inicio).json()["activa"])
                    self.assertEqual(self.client.get(carta).status_code, 403)
                    self.assertEqual(girar(self.client, partida, 0, 1).status_code, 200)

    def test_vista_previa_no_permite_recorrer_el_tablero(self):
        for dificultad in ("FACIL", "NORMAL"):
            with self.subTest(dificultad=dificultad):
                partida = crear(self.client, dificultad)
                previa = self.client.post(ruta("vista_previa", partida)).json()
                muestra = {carta["posicion"] for carta in previa["cartas"]}
                self.assertEqual(len(muestra), 4)
                self.assertNotIn("orden", previa)
                self.assertNotIn("semilla", previa)
                for posicion in range(previa["cantidad_cartas"]):
                    respuesta = self.client.get(ruta("carta_vista_previa", partida, posicion))
                    self.assertEqual(respuesta.status_code, 200 if posicion in muestra else 403)
                estado = self.client.get(ruta("estado_api", partida)).json()
                self.assertGreater(estado["espera_ms"], 0)
                self.assertEqual(estado["visibles"], [])

    def test_reintento_tras_respuesta_perdida_no_duplica_fallo(self):
        partida = crear(self.client)
        orden = partida.estado_juego["orden"]
        otra = next(i for i, clave in enumerate(orden) if clave != orden[0])
        girar(self.client, partida, 0, 1)
        respuesta = girar(self.client, partida, otra, 2)
        estado = self.client.get(ruta("estado_api", partida)).json()
        self.assertGreater(estado["espera_ms"], 0)
        self.assertEqual(estado["visibles"], [])
        self.assertEqual(estado["ultima_secuencia"], 2)
        self.assertEqual(girar(self.client, partida, otra, 2).json(), respuesta.json())
        self.assertEqual(girar(self.client, partida, 0, 2).status_code, 409)
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 2)
        partida.refresh_from_db()
        self.assertEqual(partida.errores, 1)

    def test_validacion_secuencia_posicion_y_bloqueo(self):
        partida = crear(self.client)
        orden = partida.estado_juego["orden"]
        distinta = next(i for i, clave in enumerate(orden) if clave != orden[0])
        self.assertEqual(girar(self.client, partida, 0, 2).status_code, 409)
        self.assertEqual(girar(self.client, partida, len(orden), 1).status_code, 400)
        self.assertEqual(girar(self.client, partida, 0, 1).status_code, 200)
        self.assertEqual(girar(self.client, partida, 0, 2).status_code, 400)
        self.assertEqual(girar(self.client, partida, distinta, 2).json()["tipo"], "fallo")
        self.assertEqual(girar(self.client, partida, 0, 3).status_code, 409)
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), 2)

    def test_tiempo_se_controla_en_el_servidor(self):
        partida = crear(self.client)
        Partida.objects.filter(pk=partida.pk).update(
            inicio_servidor=timezone.now() - timedelta(seconds=partida.limite_segundos + 3)
        )
        self.assertEqual(girar(self.client, partida, 0, 1, tiempo_restante=999).status_code, 400)
        respuesta = girar(self.client, partida, 0, 1)
        self.assertEqual(respuesta.status_code, 409)
        partida.refresh_from_db()
        self.assertEqual(partida.estado, Partida.Estado.TIEMPO_AGOTADO)
        self.assertEqual(partida.puntaje, 0)
        self.assertFalse(Movimiento.objects.filter(partida=partida).exists())

    def test_victoria_puntaje_unico_y_cierre(self):
        nueva = reverse("memory:nueva_partida")
        respuesta = self.client.post(nueva, {"dificultad": "FACIL", "puntaje": 999999, "estado": "GANADA"},
                                     content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Partida.objects.exists())
        partida = crear(self.client)
        posiciones = orden_por_parejas(partida)
        for secuencia, posicion in enumerate(posiciones, 1):
            manipulada = girar(self.client, partida, posicion, secuencia,
                               puntaje=999999, estado="GANADA", tiempo_restante=99999)
            self.assertEqual(manipulada.status_code, 400)
            respuesta = girar(self.client, partida, posicion, secuencia)
            self.assertEqual(respuesta.status_code, 200)
        partida.refresh_from_db()
        self.assertEqual(partida.estado, Partida.Estado.GANADA)
        self.assertGreater(partida.puntaje, 0)
        self.assertLessEqual(partida.puntaje, 1000 + 5 * partida.limite_segundos)
        cierre = (partida.puntaje, partida.fin_servidor, partida.movimientos)
        repetida = girar(self.client, partida, posiciones[-1], len(posiciones))
        self.assertEqual(repetida.json(), respuesta.json())
        self.assertEqual(girar(self.client, partida, posiciones[0], len(posiciones)).status_code, 409)
        self.assertEqual(girar(self.client, partida, 0, len(posiciones) + 1).status_code, 409)
        self.client.post(ruta("abandonar", partida))
        partida.refresh_from_db()
        self.assertEqual((partida.puntaje, partida.fin_servidor, partida.movimientos), cierre)
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), len(posiciones))

    def test_limite_de_fallos_y_derrota(self):
        partida = crear(self.client)
        orden = partida.estado_juego["orden"]
        distinta = next(i for i, clave in enumerate(orden) if clave != orden[0])
        limite = NIVELES["FACIL"]["fallos"]
        for fallo in range(1, limite + 2):
            self.assertEqual(girar(self.client, partida, 0, 2 * fallo - 1).status_code, 200)
            datos = girar(self.client, partida, distinta, 2 * fallo).json()
            self.assertEqual(datos["fallos"], fallo)
            if fallo <= limite:
                self.assertEqual(datos["estado"], Partida.Estado.EN_CURSO)
                partida.refresh_from_db()
                partida.estado_juego["bloqueado_hasta"] = None
                partida.save(update_fields=["estado_juego"])
        self.assertEqual(datos["estado"], Partida.Estado.PERDIDA)
        self.assertEqual(datos["puntaje"], 0)
        self.assertEqual(girar(self.client, partida, 0, 2 * (limite + 1) + 1).status_code, 409)

    def test_propiedad_y_abandono(self):
        partida = crear(self.client)
        ajeno = Client()
        ajeno.force_login(self.otro)
        for nombre, args in (("jugar_partida", ()), ("estado_partida", ()),
                             ("carta_vista_previa", (0,))):
            self.assertEqual(ajeno.get(ruta(nombre, partida, *args)).status_code, 404)
        self.assertEqual(ajeno.post(ruta("vista_previa", partida)).status_code, 404)
        self.assertEqual(ajeno.post(ruta("estado_partida", partida)).status_code, 404)
        self.assertEqual(girar(ajeno, partida, 0, 1).status_code, 404)
        self.assertEqual(ajeno.post(ruta("abandonar", partida)).status_code, 404)
        partida.refresh_from_db()
        self.assertEqual((partida.estado, partida.movimientos), (Partida.Estado.EN_CURSO, 0))
        abandono = self.client.post(ruta("abandonar", partida)).json()
        self.assertEqual((abandono["estado"], abandono["puntaje"]), (Partida.Estado.ABANDONADA, 0))
        self.assertEqual(girar(self.client, partida, 0, 1).status_code, 409)

    def test_post_requieren_csrf(self):
        partida = crear(self.client)
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        cliente.get(ruta("jugar_partida", partida))
        casos = [
            (reverse("memory:nueva_partida"), {"dificultad": "DIFICIL", "practica": True}),
            (ruta("estado_partida", partida), {}),
            (ruta("voltear", partida), {"posicion": 0, "seq_num": 1}),
            (ruta("vista_previa", partida), {}),
            (ruta("abandonar", partida), {}),
        ]
        for url, datos in casos:
            self.assertEqual(cliente.post(url, datos, content_type="application/json").status_code, 403)
        token = cliente.cookies["csrftoken"].value
        for url, datos in casos:
            respuesta = cliente.post(url, datos, content_type="application/json",
                                     HTTP_X_CSRFTOKEN=token)
            self.assertIn(respuesta.status_code, (200, 201))

    def test_practica_no_admite_puntaje_ni_conversion(self):
        perfil = reverse("memory:perfil")
        antes = self.client.get(perfil).context
        practica = crear(self.client, practica=True)
        intento = girar(self.client, practica, 0, 1, puntaje=999999, practica=False)
        self.assertEqual(intento.status_code, 400)
        for secuencia, posicion in enumerate(orden_por_parejas(practica), 1):
            respuesta = girar(self.client, practica, posicion, secuencia)
            self.assertEqual(respuesta.status_code, 200)
        practica.refresh_from_db()
        self.assertTrue(practica.practica)
        self.assertEqual((practica.estado, practica.puntaje), (Partida.Estado.GANADA, 0))
        self.assertEqual(respuesta.json()["puntaje"], 0)
        despues = self.client.get(perfil).context
        for campo in ("total", "victorias", "derrotas", "mejor_puntaje", "niveles", "partidas_activas"):
            self.assertEqual(despues[campo], antes[campo])


    def test_enteros_estrictos_y_json_sin_ambiguedades(self):
        partida = crear(self.client)
        for posicion in (True, "0", 0.0, None, [], -1, 16):
            with self.subTest(posicion=posicion):
                self.assertEqual(girar(self.client, partida, posicion, 1).status_code, 400)
        for secuencia in (True, "1", 1.0, None, [], 0, 10**30):
            with self.subTest(secuencia=secuencia):
                self.assertEqual(girar(self.client, partida, 0, secuencia).status_code, 400)
        url = ruta("voltear", partida)
        for cuerpo in ('{"posicion": 0, "posicion": 1, "seq_num": 1}', bytes([255]), '[]'):
            self.assertEqual(self.client.post(url, cuerpo, content_type="application/json").status_code, 400)
        self.assertFalse(Movimiento.objects.filter(partida=partida).exists())
        url = reverse("memory:nueva_partida")
        for dificultad in (True, 1, [], None, "EXTREMO"):
            respuesta = self.client.post(url, {"dificultad": dificultad}, content_type="application/json")
            self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Partida.objects.count(), 1)

    def test_consultas_get_no_guardan_vencimiento_ni_crean_perfil(self):
        partida = crear(self.client)
        PerfilJugador.objects.filter(usuario=self.usuario).delete()
        Partida.objects.filter(pk=partida.pk).update(
            inicio_servidor=timezone.now() - timedelta(seconds=partida.limite_segundos + 3)
        )
        self.client.get(reverse("memory:inicio"))
        self.client.get(ruta("jugar_partida", partida))
        perfil = self.client.get(reverse("memory:perfil")).context
        self.assertEqual((perfil["total"], perfil["derrotas"], perfil["partidas_activas"]), (1, 1, 0))
        self.assertEqual(perfil["niveles"][0]["total"], 1)
        self.assertFalse(PerfilJugador.objects.filter(usuario=self.usuario).exists())

        url = ruta("estado_partida", partida)
        estado = self.client.get(url).json()
        self.assertEqual(estado["estado"], Partida.Estado.TIEMPO_AGOTADO)
        self.assertTrue(estado["cierre_pendiente"])
        partida.refresh_from_db()
        self.assertEqual(partida.estado, Partida.Estado.EN_CURSO)
        self.assertIsNone(partida.fin_servidor)
        cierre = self.client.post(url).json()
        self.assertEqual(cierre["estado"], Partida.Estado.TIEMPO_AGOTADO)
        self.assertFalse(cierre["cierre_pendiente"])
        partida.refresh_from_db()
        self.assertIsNotNone(partida.fin_servidor)
        fin = partida.fin_servidor
        self.client.post(url)
        partida.refresh_from_db()
        self.assertEqual(partida.fin_servidor, fin)

    def test_post_de_estado_no_puede_forzar_vencimiento(self):
        partida = crear(self.client)
        respuesta = self.client.post(ruta("estado_partida", partida), {"estado": "TIEMPO_AGOTADO"})
        self.assertEqual(respuesta.json()["estado"], Partida.Estado.EN_CURSO)
        partida.refresh_from_db()
        self.assertIsNone(partida.fin_servidor)

    def test_base_de_datos_rechaza_puntaje_de_practica(self):
        practica = crear(self.client, practica=True)
        oficial = crear(self.client)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Partida.objects.filter(pk=practica.pk).update(puntaje=1)
        practica.refresh_from_db()
        self.assertEqual(practica.puntaje, 0)
        Partida.objects.filter(pk=oficial.pk).update(puntaje=1)
        oficial.refresh_from_db()
        self.assertEqual(oficial.puntaje, 1)


@override_settings(SECURE_SSL_REDIRECT=False)
class AuditoriaConcurrenciaTests(TransactionTestCase):
    def test_dos_solicitudes_simultaneas_para_el_ultimo_volteo(self):
        if not connection.features.has_select_for_update:
            self.skipTest("Requiere bloqueo de filas en la base de datos")
        usuario = preparar()
        clientes = [Client(), Client()]
        for cliente in clientes:
            cliente.force_login(usuario)
        partida = crear(clientes[0])
        posiciones = orden_por_parejas(partida)
        for secuencia, posicion in enumerate(posiciones[:-1], 1):
            self.assertEqual(girar(clientes[0], partida, posicion, secuencia).status_code, 200)
        barrera = Barrier(2)

        def finalizar(cliente):
            close_old_connections()
            try:
                barrera.wait(timeout=10)
                respuesta = girar(cliente, partida, posiciones[-1], len(posiciones))
                return respuesta.status_code, respuesta.json()
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(ejecutor.map(finalizar, clientes))
        self.assertEqual(resultados[0], resultados[1])
        self.assertEqual(resultados[0][0], 200)
        partida.refresh_from_db()
        self.assertEqual(partida.estado, Partida.Estado.GANADA)
        self.assertEqual(partida.movimientos, len(posiciones))
        self.assertEqual(Movimiento.objects.filter(partida=partida).count(), len(posiciones))
        self.assertEqual(partida.puntaje, resultados[0][1]["puntaje"])
        self.assertGreater(partida.puntaje, 0)
