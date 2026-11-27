#!/usr/bin/env bash
# Recolecta las evidencias técnicas del servidor Oracle (CPU, memoria, disco,
# kernel, redes, volúmenes y docker stats) en un solo archivo de texto.
#
# Uso (en el servidor Ubuntu de Oracle, dentro de ~/sonic-memory-card):
#   bash scripts/recolectar_evidencias_oracle.sh
#   bash scripts/recolectar_evidencias_oracle.sh grupo1-ordenes-nuevo   # si usan otro nombre de proyecto
#
# Solo lee información: no detiene, borra ni modifica contenedores o volúmenes.
# Revisen el archivo antes de subirlo a GitHub por si aparece algún dato privado.

set -u
PROYECTO="${1:-}"
DC="sudo docker compose"
[ -n "$PROYECTO" ] && DC="sudo docker compose -p $PROYECTO"

FECHA="$(date '+%Y-%m-%d_%H%M')"
SALIDA="docs/evidencias/registros/oracle-${FECHA}.txt"
mkdir -p "$(dirname "$SALIDA")"

seccion() { printf '\n\n===== %s =====\n$ %s\n' "$1" "$2"; bash -c "$2" 2>&1; }

{
  echo "# Evidencias del servidor Oracle Cloud — $(date '+%Y-%m-%d %H:%M %Z')"
  seccion "Kernel y sistema operativo" "uname -a; echo; cat /etc/os-release | head -4"
  seccion "CPU" "lscpu | grep -E 'Architecture|Model name|^CPU\(s\)|Thread|Core'"
  seccion "Memoria" "free -h"
  seccion "Disco" "df -h / /var/lib/docker 2>/dev/null"
  seccion "Tiempo encendido y carga" "uptime"
  seccion "Versión de Docker" "sudo docker version --format 'Cliente {{.Client.Version}} / Servidor {{.Server.Version}}'; $DC version"
  seccion "Servicios del proyecto" "$DC ps"
  seccion "Consumo de recursos de los contenedores" "sudo docker stats --no-stream"
  seccion "Límites de memoria y CPU configurados" "for c in \$($DC ps -q); do sudo docker inspect --format '{{.Name}}  memoria={{.HostConfig.Memory}}  nanoCPUs={{.HostConfig.NanoCpus}}' \$c; done"
  seccion "Redes de Docker" "sudo docker network ls"
  seccion "Red backend interna (PostgreSQL aislado)" "sudo docker network inspect \$(sudo docker network ls -q --filter name=backend) --format '{{.Name}} internal={{.Internal}}' 2>/dev/null"
  seccion "Volúmenes de Docker" "sudo docker volume ls"
  seccion "Puertos escuchando en el host (5432 no debe aparecer público)" "sudo ss -tlnp | grep -E ':(80|443|5432|8000|8081)\\b' || true"
  seccion "Salud de la aplicación" "curl -s -w '  HTTP %{http_code}\n' --max-time 15 https://159-54-142-136.sslip.io/salud/"
  seccion "Cabeceras HTTPS" "curl -sIL --max-time 20 https://159-54-142-136.sslip.io/ | grep -iE '^(HTTP|location|strict-transport|server)'"
  seccion "Últimos registros de Django" "$DC logs --tail=20 web"
} > "$SALIDA"

echo "Evidencias guardadas en: $SALIDA"
echo "Para la evidencia visual: capturen la terminal mientras corre 'sudo docker stats' y 'sudo docker compose ps'."
