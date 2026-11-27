"""Prueba de carga moderada: N solicitudes concurrentes contra rutas públicas."""
import sys, time, statistics, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
base, total, conc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rutas = ["/salud/", "/cuentas/login/", "/cuentas/registro/"]
def pedir(i):
    url = base + rutas[i % len(rutas)]; t = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=15) as r: r.read(); c = r.status
    except urllib.error.HTTPError as e: c = e.code
    except Exception: c = "error"
    return c, (time.perf_counter() - t) * 1000
t0 = time.perf_counter()
with ThreadPoolExecutor(conc) as ex: res = list(ex.map(pedir, range(total)))
dur = time.perf_counter() - t0
lat = sorted(r[1] for r in res); codigos = {}
for c, _ in res: codigos[c] = codigos.get(c, 0) + 1
print(f"Solicitudes: {total} | Concurrencia: {conc} | Rutas: {', '.join(rutas)}")
print(f"Duración total: {dur:.2f} s | Rendimiento: {total/dur:.1f} solicitudes/s")
print(f"Latencia ms -> media {statistics.mean(lat):.1f} | p50 {lat[len(lat)//2]:.1f} | p95 {lat[int(len(lat)*.95)]:.1f} | máx {lat[-1]:.1f}")
print(f"Códigos HTTP: {codigos}")
