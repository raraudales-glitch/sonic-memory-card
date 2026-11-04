# Sonic Memory Card

**Proyecto 1 — Memory Game: emparejamiento de cartas**  
**Asignatura:** Arquitectura de Computadoras · Ingeniería en Computación · UTH  
**Repositorio:** https://github.com/raraudales-glitch/sonic-memory-card

> **Estado:** En desarrollo. El repositorio contiene la base de Django, PostgreSQL y los modelos del juego, pero **todavía no incluye una partida jugable, las rutas del juego ni su API**. La configuración de Docker actual es para **desarrollo local**, no para producción.

## 1. Descripción

Sonic Memory Card es un proyecto académico de juego de memoria de un solo jugador con temática visual inspirada en Sonic. El objetivo es encontrar parejas de cartas iguales antes de que termine el tiempo o se exceda el límite de fallos.

De acuerdo con la guía del **Proyecto Final de Arquitectura de Computadoras**, la lógica y los datos privados de la partida deben mantenerse en **Django**. El navegador mostrará las cartas y animaciones, pero no decidirá si una jugada es válida ni calculará el resultado o la puntuación.

El propósito académico incluye demostrar el funcionamiento del juego y su infraestructura: Linux, Docker, redes, volúmenes, proxy inverso, persistencia, monitoreo, actualización y recuperación.

## 2. Tecnologías

| Tecnología | Uso | Estado actual |
|---|---|---|
| Python 3.12 | Backend | Configurada en `Dockerfile` |
| Django 5.2 LTS | Framework y administración | Incluido en dependencias |
| PostgreSQL 16 | Persistencia | Servicio `db` en Compose |
| Psycopg 3 | Conexión Django–PostgreSQL | Incluido en dependencias |
| Docker y Docker Compose | Contenedores `web` y `db` | Configurados para desarrollo |
| HTML, CSS y JavaScript | Interfaz del juego | Pendiente |
| Gunicorn | Servidor WSGI de producción | Instalado como dependencia, aún no utilizado |
| Caddy o Nginx | Proxy inverso, HTTPS y estáticos | Pendiente |
| Linux en la nube | Servidor de producción | Pendiente |

## 3. Funcionalidades implementadas

En el código publicado actualmente existen:

- **`PerfilJugador`**: vínculo con el usuario Django, alias y preferencias de audio.
- **`Personaje`**: catálogo de personajes para las cartas, con nombre, origen e imagen.
- **`Partida`**: usuario, dificultad, estado, inicio, límite de tiempo, duración, errores, movimientos, puntuación y estado JSON.
- **`Movimiento`**: número de secuencia, tipo, datos y fecha de cada movimiento.
- Restricción de base de datos para impedir **más de una partida `EN_CURSO` por usuario**.
- Restricción para impedir números de movimiento duplicados en una misma partida.
- Modelos registrados en el **panel administrativo de Django**.
- Migración inicial y volumen Docker para persistir los datos de PostgreSQL.

**Importante:** tener estos modelos no significa que el juego, las validaciones o las estadísticas ya funcionen desde la interfaz.

## 4. Reglas del Proyecto 1 (por implementar)

El jugador voltea dos cartas por turno. Una pareja correcta queda descubierta; si las cartas son distintas, se registra un fallo y se vuelven a ocultar. El servidor debe generar y conservar el orden completo del tablero, revelar solo lo permitido y rechazar acciones inválidas (repetir una carta, seleccionar una ya emparejada o una tercera carta en el mismo turno).

### Niveles obligatorios

| Parámetro | Fácil | Normal | Difícil |
|---|---:|---:|---:|
| Tablero | 4 × 4 | 4 × 5 | 6 × 6 |
| Parejas | 8 | 10 | 18 |
| Tiempo límite | 150 s | 150 s | 210 s |
| Fallos permitidos | 16 | 15 | 22 |
| Vista previa inicial | 3 s | 1.5 s | Sin vista previa |
| Visualización de un fallo | 1.0 s | 0.8 s | 0.6 s |
| Multiplicador | ×1.0 | ×1.5 | ×2.0 |

### Resultados y puntuación

- **GANADA:** todas las parejas encontradas dentro del límite de tiempo y sin superar los fallos permitidos.
- **PERDIDA:** se supera el límite de fallos.
- **TIEMPO_AGOTADO:** el servidor detecta que terminó el tiempo.
- **ABANDONADA:** el jugador abandona o inicia una nueva partida.
- **EN_CURSO:** la partida admite jugadas válidas.

Solo una partida **GANADA** puede recibir puntos. Su fórmula es:

```text
Puntaje = (1000 + 5 × segundos_restantes − 25 × fallos) × multiplicador
Puntaje mínimo si gana = 100 × multiplicador
Puntaje si pierde, abandona o agota el tiempo = 0
```

El servidor debe calcular y almacenar el puntaje **una sola vez**. La recarga del navegador no debe reiniciar el tiempo; las acciones posteriores al final de la partida deben rechazarse. La guía contempla una tolerancia de **2 segundos** por latencia de red.

## 5. Requisitos para ejecución local

- **Git** instalado.
- **Docker Desktop** con el motor Linux activo, o Docker Engine con Compose v2.
- Puerto **8000** disponible.
- No se requiere instalar Python ni PostgreSQL en el equipo si se utiliza Docker.

### Instalación con PowerShell (Windows)

**1. Descargar el proyecto:**

```powershell
git clone https://github.com/raraudales-glitch/sonic-memory-card.git
cd sonic-memory-card
```

Si ya tienes una copia con cambios locales, utiliza esa carpeta en vez de volver a clonarla.

**2. Crear las variables de entorno:**

```powershell
Copy-Item .env.example .env
notepad .env
```

El archivo `.env.example` actual contiene:

```dotenv
POSTGRES_DB=sonicmemory
POSTGRES_USER=CAMBIAR_USUARIO
POSTGRES_PASSWORD=CAMBIAR_CONTRASENA
DB_HOST=db
DB_PORT=5432
DJANGO_SECRET_KEY=CAMBIAR_SECRET_KEY
DJANGO_DEBUG=True
```

Sustituye los valores `CAMBIAR_*` por datos privados. **Nunca publiques `.env` ni una clave o contraseña real en GitHub.** Para el entorno local, conserva `DB_HOST=db` y `DB_PORT=5432`.

**3. Construir e iniciar los contenedores:**

```powershell
docker compose up -d --build
docker compose ps
```

**4. Aplicar las migraciones:**

```powershell
docker compose exec web python manage.py migrate
```

**5. Crear un administrador:**

```powershell
docker compose exec web python manage.py createsuperuser
```

**6. Abrir el panel:**

- Administración: **http://localhost:8000/admin/**
- La ruta `http://localhost:8000/` todavía **no está implementada** y puede devolver **404**.

Esta instalación **solo permite verificar la base administrativa**; aún no existe una partida jugable.

## 6. Comandos de administración local

| Acción | Comando |
|---|---|
| Iniciar servicios | `docker compose up -d` |
| Reconstruir e iniciar | `docker compose up -d --build` |
| Estado de contenedores | `docker compose ps` |
| Registros de Django | `docker compose logs -f web` |
| Registros de PostgreSQL | `docker compose logs -f db` |
| Revisar recursos | `docker stats --no-stream` |
| Ejecutar migraciones | `docker compose exec web python manage.py migrate` |
| Ejecutar pruebas existentes | `docker compose exec web python manage.py test` |
| Detener sin borrar los datos | `docker compose down` |

> **Precaución:** `docker compose down -v` elimina los volúmenes de Compose y puede borrar la base de datos. No lo ejecutes si necesitas conservar usuarios y partidas.

La orden de pruebas está disponible, pero **todavía no hay una suite de pruebas implementada** para las reglas del juego.

## 7. Estructura actual del repositorio

```text
sonic-memory-card/
├── config/                 # settings.py, urls.py, wsgi.py
├── memory/                 # models.py, admin.py, views.py, tests.py, migrations/
├── .env.example            # Variables de ejemplo, sin secretos
├── .gitignore              # Exclusiones de Git
├── Dockerfile              # Imagen Python/Django (desarrollo)
├── docker-compose.yml      # Servicios db y web
├── manage.py               # Comandos de administración Django
├── requirements.txt        # Dependencias Python
└── README.md               # Este documento (al incorporarlo al repositorio)
```

## 8. Arquitectura: actual y requerida

**Arquitectura local actual:**

```text
Navegador -> localhost:8000 -> Django runserver (web)
                                   |
                                   v
                            PostgreSQL (db)
                                   |
                                   v
                         volumen postgres_data
```

**Arquitectura obligatoria para producción (aún pendiente):**

```text
Navegador (HTTPS)
       |
       v
Proxy inverso (Caddy/Nginx, puertos 80/443)
       |
       v
Gunicorn + Django (red interna)
       |
       v
PostgreSQL 16 (red backend privada)
       |
       v
Volumen persistente para la base de datos
```

Para cumplir la guía, solo el proxy debe exponer los puertos públicos; PostgreSQL no debe tener un mapeo `ports:`. También se necesitan volúmenes para archivos estáticos, usuario sin privilegios, healthchecks y límites de CPU/RAM.

**El `docker-compose.yml` actual ejecuta `python manage.py runserver` y publica el puerto 8000**, por lo que **no debe usarse tal como está para desplegar en internet**.

## 9. Rutas exigidas por la guía (pendientes)

| Método y ruta | Función |
|---|---|
| `GET /` | Inicio |
| `GET, POST /cuentas/registro/` | Registro |
| `GET, POST /cuentas/login/` | Iniciar sesión |
| `POST /cuentas/logout/` | Cerrar sesión |
| `GET /instrucciones/` | Reglas y controles |
| `GET /jugar/` | Selección de nivel |
| `POST /partidas/nueva/` | Crear partida |
| `GET /partidas/<uuid>/` | Tablero de la partida |
| `GET /api/partidas/<uuid>/estado/` | Estado y tiempo restante |
| `POST /api/partidas/<uuid>/accion/` | Voltear carta con número de secuencia |
| `POST /api/partidas/<uuid>/abandonar/` | Abandonar partida |
| `GET /partidas/<uuid>/resultado/` | Resultado final |
| `GET /perfil/` | Perfil y estadísticas |
| `GET /historial/` | Partidas anteriores |
| `GET /clasificacion/?nivel=facil` | Clasificación por dificultad |
| `GET /salud/` | Comprobación del servicio y la base |

Actualmente solo está registrada la ruta **`/admin/`**.

## 10. Lista de trabajo para cumplir la guía

### Juego y usuarios

- [ ] Registro, inicio y cierre de sesión; privacidad entre usuarios.
- [ ] Pantallas de inicio, instrucciones y selección de nivel.
- [ ] Interfaz adaptable desde 360 px, controles de ratón y pantalla táctil.
- [ ] Generar y barajar las cartas en Django sin enviar el orden completo al navegador.
- [ ] Validar volteos y jugadas repetidas; controlar el tiempo con la hora del servidor.
- [ ] Implementar tres niveles con los parámetros oficiales.
- [ ] Calcular puntaje, victoria, derrota, tiempo agotado y abandono en el servidor.
- [ ] Crear resultado, historial paginado, estadísticas y clasificación por dificultad.
- [ ] Incorporar animaciones, sonidos, música y controles separados de volumen.
- [ ] Crear `CREDITOS.md` con fuente y licencia de recursos audiovisuales.

### Infraestructura y publicación

- [ ] Usar **Gunicorn** en el contenedor de producción en lugar de `runserver`.
- [ ] Ejecutar Django bajo un **usuario sin privilegios**.
- [ ] Incorporar **Caddy o Nginx**, redes `frontend` y `backend`, estáticos y healthchecks.
- [ ] Configurar límites de CPU y memoria en Compose.
- [ ] Preparar ajustes de producción: `DJANGO_DEBUG=False`, hosts y orígenes CSRF autorizados.
- [ ] Publicar en un servidor Linux con acceso SSH, dominio y **HTTPS** válido.
- [ ] Comprobar acceso externo y que PostgreSQL no publique el puerto 5432.
- [ ] Configurar y probar respaldo/restauración de la base de datos.

### Calidad, evidencias y entregables

- [ ] Implementar **al menos 10 pruebas automatizadas** con `python manage.py test`.
- [ ] Verificar los casos específicos M1–M6 del Memory Game y las pruebas comunes C01–C17.
- [ ] Capturar evidencia de CPU, memoria, disco, kernel, redes, volúmenes y `docker stats`.
- [ ] Ejecutar una prueba de carga moderada y un fallo controlado documentado.
- [ ] Demostrar actualización sin pérdida de datos y restauración desde respaldo.
- [ ] Elaborar informe técnico de **mínimo 15 páginas** y bitácora de uso de IA.
- [ ] Preparar presentación de **mínimo 10 diapositivas** y defensa grupal.
- [ ] Registrar los aportes del equipo mediante commits.
- [ ] Documentar **URL pública y usuario de prueba** cuando existan, sin publicar contraseñas privadas.

## 11. Despliegue y recuperación (procedimientos futuros)

Estos pasos **todavía no están habilitados** en la configuración publicada. Se usarán después de implementar y probar los servicios de producción de la sección 8.

En el **servidor Linux**, se deberá verificar el estado de los servicios y preparar la base y los archivos estáticos:

```bash
docker compose build web
docker compose up -d
docker compose ps
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check --deploy
```

Para monitorear y diagnosticar:

```bash
docker compose logs -f web
docker compose logs proxy
docker stats --no-stream
docker network ls
docker volume ls
```

Para reiniciar la aplicación y actualizar conservando el volumen de base de datos:

```bash
docker compose restart web
git pull
docker compose build web
docker compose up -d web
docker compose exec web python manage.py migrate
```

El procedimiento de respaldo utilizará `pg_dump` y el de recuperación `pg_restore`. Antes de ejecutarlos se deberán **probar con datos de ensayo**, establecer los nombres reales de las variables y conservar una copia fuera del servidor. Una restauración con `--clean` puede reemplazar datos existentes; **nunca se debe ejecutar sin confirmar el respaldo**.

## 12. Evaluación y fuentes

Esta implementación se desarrolla siguiendo la **Guía General del Proyecto Final de Arquitectura de Computadoras, UTH**, especialmente:

- Sección 4: tecnologías, funcionalidades, estados, puntuación y rutas comunes.
- Sección 5.1: ficha del **Proyecto 1, Memory Game**.
- Secciones 6 y 7: infraestructura, despliegue, administración y recuperación.
- Sección 8: pruebas comunes y automatizadas.
- Secciones 10 a 14: revisiones, entregables, rúbrica y lista de verificación.

**Aviso sobre recursos:** Sonic y sus personajes pertenecen a sus titulares de derechos. Este repositorio es un trabajo académico no oficial, sin afiliación con SEGA. Los materiales usados en el juego deben contar con autorización o licencias adecuadas y quedar atribuidos en `CREDITOS.md`.
