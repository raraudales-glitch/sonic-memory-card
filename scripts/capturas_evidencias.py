"""Genera capturas de evidencia del juego en una instalación local y juega
partidas completas para verificar el TOP 5 por nivel.

Uso: python scripts/capturas_evidencias.py <carpeta>
Requiere playwright, el servidor en 127.0.0.1:8000, cuentas de prueba con la
clave CLAVE y acceso psql a la base local (ajustar puerto/usuario en orden())."""
import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
CLAVE = "Prueba#2026x"


def orden(pid):
    q = f"select estado_juego->'orden' from memory_partida where id='{pid}'"
    r = subprocess.run(["psql", "-h", "127.0.0.1", "-p", "5433", "-U", "postgres", "-d", "sonicmemory",
                        "-tAc", q], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def login(page, usuario):
    page.goto(BASE + "/cuentas/login/")
    page.fill("[name=username]", usuario)
    page.fill("[name=password]", CLAVE)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")


def nueva(page, nivel):
    page.goto(BASE + "/")
    page.wait_for_load_state("networkidle")
    page.click(f"button.dificultad.{nivel.lower()}")
    page.wait_for_url("**/partidas/*/", timeout=15000)
    return page.url.rstrip("/").split("/")[-1]


def jugar(page, nivel, captura=None, fallos=0):
    pid = nueva(page, nivel)
    page.wait_for_timeout(4500)  # vista previa
    if captura:
        page.screenshot(path=OUT / f"{captura}-inicio.png")
    cartas = orden(pid)
    pares = {}
    for i, c in enumerate(cartas):
        pares.setdefault(c, []).append(i)
    lista = list(pares.values())
    # fallos intencionales para variar puntajes
    for k in range(fallos):
        a, b = lista[k][0], lista[k + 1][0]
        page.click(f".carta[data-posicion='{a}']"); page.wait_for_timeout(250)
        page.click(f".carta[data-posicion='{b}']"); page.wait_for_timeout(1500)
    for n, (a, b) in enumerate(lista):
        page.click(f".carta[data-posicion='{a}']"); page.wait_for_timeout(250)
        page.click(f".carta[data-posicion='{b}']"); page.wait_for_timeout(450)
        if captura and n == len(lista) // 2:
            page.screenshot(path=OUT / f"{captura}-en-juego.png")
    page.wait_for_selector("text=Ver resultado", timeout=20000)
    page.wait_for_timeout(1200)
    if captura:
        page.screenshot(path=OUT / f"{captura}-victoria.png")
    page.goto(f"{BASE}/partidas/{pid}/resultado/")
    page.wait_for_load_state("networkidle"); page.wait_for_timeout(800)
    if captura:
        page.screenshot(path=OUT / f"{captura}-resultado.png", full_page=True)
    return pid


with sync_playwright() as p:
    nav = p.chromium.launch(args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    pc = nav.new_context(viewport={"width": 1366, "height": 800})
    page = pc.new_page()

    page.goto(BASE + "/cuentas/login/"); page.wait_for_load_state("networkidle")
    page.screenshot(path=OUT / "01-login.png")
    page.goto(BASE + "/cuentas/registro/"); page.wait_for_load_state("networkidle")
    page.screenshot(path=OUT / "02-registro.png")

    login(page, "sonic_tester")
    page.screenshot(path=OUT / "03-inicio-seleccion-nivel.png")
    page.goto(BASE + "/instrucciones/"); page.wait_for_load_state("networkidle")
    page.screenshot(path=OUT / "04-instrucciones.png", full_page=True)

    jugar(page, "FACIL", "05-facil")
    jugar(page, "NORMAL", "06-normal", fallos=1)
    jugar(page, "DIFICIL", "07-dificil", fallos=2)

    # Más jugadores para llenar el TOP 5 de cada nivel
    for usuario, extra in (("tails_tester", 2), ("amy_tester", 4)):
        ctx = nav.new_context(viewport={"width": 1366, "height": 800})
        pg = ctx.new_page(); login(pg, usuario)
        for nivel in ("FACIL", "NORMAL", "DIFICIL"):
            jugar(pg, nivel, fallos=extra)
        ctx.close()

    for ruta, nombre in (("/perfil/", "08-perfil"), ("/historial/", "09-historial"),
                         ("/clasificacion/?nivel=facil", "10-clasificacion-facil"),
                         ("/clasificacion/?nivel=dificil", "11-clasificacion-dificil"),
                         ("/top-semanal/", "12-top5-semanal"), ("/salud/", "13-salud")):
        page.goto(BASE + ruta); page.wait_for_load_state("networkidle"); page.wait_for_timeout(500)
        page.screenshot(path=OUT / f"{nombre}.png", full_page=True)

    adm = nav.new_context(viewport={"width": 1366, "height": 800}).new_page()
    adm.goto(BASE + "/admin/login/"); adm.fill("#id_username", "admin_demo"); adm.fill("#id_password", CLAVE)
    adm.click("input[type=submit]"); adm.wait_for_load_state("networkidle")
    adm.screenshot(path=OUT / "14-panel-admin.png", full_page=True)
    adm.goto(BASE + "/admin/memory/partida/"); adm.wait_for_load_state("networkidle")
    adm.screenshot(path=OUT / "15-admin-partidas.png")

    movil = nav.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                            is_mobile=True, has_touch=True).new_page()
    login(movil, "amy_tester")
    movil.screenshot(path=OUT / "16-movil-inicio.png")
    pid = nueva(movil, "NORMAL"); movil.wait_for_timeout(3000)
    movil.screenshot(path=OUT / "17-movil-tablero.png")
    nav.close()
print("listo")
