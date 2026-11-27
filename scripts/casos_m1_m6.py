"""Ejecuta los casos M1–M6 de la guía (Memory Game) por HTTP contra una
instalación del juego y escribe un registro con las respuestas reales.

Uso: python scripts/casos_m1_m6.py http://127.0.0.1:8000 usuario1 usuario2 clave

Para forzar M2, M4 y M5 el script consulta el orden de las cartas directamente
en PostgreSQL (como lo haría un probador con acceso al servidor). El jugador
nunca recibe ese orden por la API: eso es justamente lo que comprueba M3.
"""
import json
import subprocess
import sys
import threading
import time

import requests

BASE, USUARIO, USUARIO_M6, CLAVE = sys.argv[1:5]
PSQL = ["psql", "-h", "127.0.0.1", "-p", "5433", "-U", "postgres", "-d", "sonicmemory", "-tAc"]
LINEAS, CANDADO = [], threading.Lock()


def log(texto=""):
    with CANDADO:
        LINEAS.append(texto)
        print(texto, flush=True)


def sql(consulta):
    return subprocess.run(PSQL + [consulta], capture_output=True, text=True, check=True).stdout.strip()


def sesion(usuario):
    s = requests.Session()
    s.get(f"{BASE}/cuentas/login/")
    s.post(f"{BASE}/cuentas/login/", data={"username": usuario, "password": CLAVE,
           "csrfmiddlewaretoken": s.cookies["csrftoken"]}, headers={"Referer": BASE})
    return s


def post(s, ruta, datos=None):
    return s.post(BASE + ruta, json=datos or {}, headers={"X-CSRFToken": s.cookies["csrftoken"], "Referer": BASE})


def nueva(s, dificultad):
    r = post(s, "/partidas/nueva/", {"dificultad": dificultad, "practica": False})
    return r.json()["partida"]["id"]


class Jugador:
    def __init__(self, s, pid):
        self.s, self.pid, self.seq = s, pid, 0

    def voltear(self, pos, seq=None):
        if seq is None:
            self.seq += 1
            seq = self.seq
        return post(self.s, f"/api/partidas/{self.pid}/accion/", {"posicion": pos, "seq_num": seq})


def resumen(r, *claves):
    d = r.json()
    return f"HTTP {r.status_code} → " + json.dumps({k: d.get(k) for k in claves if k in d}, ensure_ascii=False)


def pares(pid):
    orden = json.loads(sql(f"select estado_juego->'orden' from memory_partida where id='{pid}'"))
    grupos = {}
    for i, c in enumerate(orden):
        grupos.setdefault(c, []).append(i)
    return list(grupos.values()), orden


def caso_m6(resultado):
    s = sesion(USUARIO_M6)
    pid = nueva(s, "FACIL")
    limite = int(sql(f"select limite_segundos from memory_partida where id='{pid}'"))
    resultado["inicio"] = time.strftime("%H:%M:%S")
    resultado["limite"] = limite
    time.sleep(limite + 3)
    j = Jugador(s, pid)
    e = s.get(f"{BASE}/api/partidas/{pid}/estado/").json()
    resultado["estado_get"] = {k: e[k] for k in ("estado", "tiempo_restante", "cierre_pendiente")}
    r = j.voltear(0)
    resultado["accion"] = resumen(r, "ok", "error", "estado", "tiempo_restante", "puntaje")
    resultado["fin"] = time.strftime("%H:%M:%S")
    resultado["bd"] = sql(f"select estado||' | puntaje='||coalesce(puntaje::text,'NULL') from memory_partida where id='{pid}'")


m6 = {}
hilo = threading.Thread(target=caso_m6, args=(m6,))
hilo.start()

s = sesion(USUARIO)
log(f"# Casos M1–M6 del Memory Game — ejecutados por HTTP contra {BASE}")
log(f"# Fecha: {time.strftime('%Y-%m-%d %H:%M')} (hora de Tegucigalpa) · Jugador: {USUARIO} (M6: {USUARIO_M6})")

# M1 ---------------------------------------------------------------
log("\n## M1 — Voltear la misma carta dos veces\nEsperado: la segunda acción se rechaza sin contar fallo.")
j = Jugador(s, nueva(s, "DIFICIL"))
log("  1.er volteo posición 0: " + resumen(j.voltear(0), "ok", "tipo", "fallos"))
r = j.voltear(0)
log("  2.º volteo posición 0:  " + resumen(r, "ok", "error"))
e = s.get(f"{BASE}/api/partidas/{j.pid}/estado/").json()
log(f"  Estado después: fallos={e['fallos']}, ultima_secuencia={e['ultima_secuencia']}")
m1 = r.status_code == 400 and e["fallos"] == 0
log(f"  RESULTADO M1: {'CUMPLE' if m1 else 'NO CUMPLE'}")
post(s, f"/api/partidas/{j.pid}/abandonar/")

# M2 ---------------------------------------------------------------
log("\n## M2 — Voltear una carta ya emparejada\nEsperado: respuesta 400 con mensaje; estado sin cambios.")
j = Jugador(s, nueva(s, "DIFICIL"))
grupos, _ = pares(j.pid)
a, b = grupos[0]
j.voltear(a)
log(f"  Pareja en posiciones {a} y {b}: " + resumen(j.voltear(b), "ok", "tipo", "parejas_encontradas"))
antes = s.get(f"{BASE}/api/partidas/{j.pid}/estado/").json()
r = j.voltear(a)
despues = s.get(f"{BASE}/api/partidas/{j.pid}/estado/").json()
log(f"  Volteo de nuevo la posición {a}: " + resumen(r, "ok", "error"))
campos = ("fallos", "parejas_encontradas", "ultima_secuencia", "estado")
log("  Estado antes:   " + json.dumps({k: antes[k] for k in campos}))
log("  Estado después: " + json.dumps({k: despues[k] for k in campos}))
m2 = r.status_code == 400 and all(antes[k] == despues[k] for k in campos)
log(f"  RESULTADO M2: {'CUMPLE' if m2 else 'NO CUMPLE'}")
post(s, f"/api/partidas/{j.pid}/abandonar/")

# M3 ---------------------------------------------------------------
log("\n## M3 — Intentar ver el tablero con las herramientas del navegador\n"
    "Esperado: la respuesta JSON no contiene el orden completo.")
j = Jugador(s, nueva(s, "DIFICIL"))
_, orden = pares(j.pid)
html = s.get(f"{BASE}/partidas/{j.pid}/").text
estado = s.get(f"{BASE}/api/partidas/{j.pid}/estado/")
accion = j.voltear(0)
log(f"  Tablero Difícil de {len(orden)} cartas.")
log(f"  HTML de la página: contiene 'orden'={'\"orden\"' in html}, contiene datos de posición={'\"posicion\":' in html}")
claves_estado = [c["clave"] for c in estado.json()["emparejadas"] + estado.json()["visibles"]]
log(f"  GET /api/partidas/<id>/estado/: claves de cartas recibidas={len(claves_estado)} de {len(orden)}; "
    f"campos={sorted(estado.json())}")
log(f"  POST /api/partidas/<id>/accion/ (1 volteo): cartas reveladas=1 → {accion.json()['carta']['clave']}; "
    f"contiene 'orden'={'orden' in accion.json()}, contiene 'semilla'={'semilla' in accion.json()}")
m3 = '"orden"' not in html and len(claves_estado) == 0 and "orden" not in accion.json()
log(f"  RESULTADO M3 (estado, acciones y HTML): {'CUMPLE' if m3 else 'NO CUMPLE'}")
post(s, f"/api/partidas/{j.pid}/abandonar/")
log("  Nota sobre la vista previa (exigida por la guía: 3 s en Fácil y 1,5 s en Normal):")
jf = Jugador(s, nueva(s, "FACIL"))
p1 = post(s, f"/partidas/{jf.pid}/vista-previa/")
p2 = post(s, f"/partidas/{jf.pid}/vista-previa/")
log(f"    1.ª solicitud POST /vista-previa/: activa={p1.json()['activa']}, cartas={len(p1.json()['cartas'])}, "
    f"Cache-Control='{p1.headers.get('Cache-Control')}', contiene semilla={'semilla' in p1.json()}")
log(f"    2.ª solicitud POST /vista-previa/: activa={p2.json()['activa']}, cartas={len(p2.json()['cartas'])}")
log("    Para mostrar todas las cartas durante la vista previa el navegador tiene que recibirlas una sola vez.\n"
    "    Fuera de esa ventana ninguna respuesta vuelve a entregarlas, y en Difícil no existe vista previa.")
post(s, f"/api/partidas/{jf.pid}/abandonar/")

# M4 ---------------------------------------------------------------
log("\n## M4 — Alcanzar fallos permitidos + 1\nEsperado: partida PERDIDA; nuevas acciones responden 409.")
j = Jugador(s, nueva(s, "DIFICIL"))
grupos, _ = pares(j.pid)
permitidos = s.get(f"{BASE}/api/partidas/{j.pid}/estado/").json()["fallos_maximos"]
for k in range(permitidos + 1):
    j.voltear(grupos[0][0])
    r = j.voltear(grupos[1][0])
    time.sleep(0.65)
log(f"  Fallos permitidos en Difícil: {permitidos}. Fallo n.º {permitidos + 1}: " + resumen(r, "estado", "fallos", "puntaje"))
r2 = j.voltear(grupos[2][0])
log("  Nueva acción después de perder: " + resumen(r2, "ok", "error", "estado"))
m4 = r.json()["estado"] == "PERDIDA" and r2.status_code == 409
log(f"  RESULTADO M4: {'CUMPLE' if m4 else 'NO CUMPLE'}")

# M5 ---------------------------------------------------------------
log("\n## M5 — Encontrar todas las parejas\nEsperado: partida GANADA y puntaje según la fórmula.")
j = Jugador(s, nueva(s, "NORMAL"))
post(s, f"/partidas/{j.pid}/vista-previa/")
time.sleep(1.6)
grupos, _ = pares(j.pid)
for k in range(3):  # tres fallos intencionales
    j.voltear(grupos[k][0]); j.voltear(grupos[k + 1][0]); time.sleep(0.85)
for a, b in grupos:
    j.voltear(a); r = j.voltear(b)
d = r.json()
fila = sql(f"select limite_segundos||'|'||duracion_segundos||'|'||errores||'|'||puntaje from memory_partida where id='{j.pid}'")
limite, duracion, fallos, puntaje = map(int, fila.split("|"))
restantes = d["tiempo_restante"]
esperado = max(round((1000 + 5 * restantes - 25 * fallos) * 1.5), 150)
log("  Última pareja: " + resumen(r, "estado", "fallos", "parejas_encontradas", "tiempo_restante", "puntaje"))
log(f"  Cálculo manual: (1000 + 5 × {restantes} − 25 × {fallos}) × 1,5 = {esperado}  ·  puntaje guardado = {puntaje}")
m5 = d["estado"] == "GANADA" and puntaje == esperado
log(f"  RESULTADO M5: {'CUMPLE' if m5 else 'NO CUMPLE'}")

# M6 ---------------------------------------------------------------
log("\n## M6 — Dejar correr el tiempo\nEsperado: partida TIEMPO_AGOTADO; puntaje 0.")
hilo.join()
log(f"  Partida Fácil creada a las {m6['inicio']} con límite de {m6['limite']} s; sin jugar hasta las {m6['fin']}.")
log(f"  GET /estado/ al vencer: {json.dumps(m6['estado_get'], ensure_ascii=False)}")
log(f"  Intento de volteo después del límite: {m6['accion']}")
log(f"  Registro en PostgreSQL: {m6['bd']}")
m6ok = "TIEMPO_AGOTADO" in m6["bd"] and "puntaje=0" in m6["bd"]
log(f"  RESULTADO M6: {'CUMPLE' if m6ok else 'NO CUMPLE'}")

log("\n## Resumen")
for n, ok in (("M1", m1), ("M2", m2), ("M3", m3), ("M4", m4), ("M5", m5), ("M6", m6ok)):
    log(f"  {n}: {'CUMPLE' if ok else 'NO CUMPLE'}")

if len(sys.argv) > 5:
    open(sys.argv[5], "w", encoding="utf-8").write("\n".join(LINEAS) + "\n")
