# Sonic Memory Card

**Proyecto 1: Memory Game (emparejamiento de cartas)**  
**Asignatura:** Arquitectura de Computadoras  
**Carrera:** Ingeniería en Computación  
**Universidad:** Universidad Tecnológica de Honduras (UTH)  
**Repositorio:** https://github.com/raraudales-glitch/sonic-memory-card

> **Estado del proyecto:** En desarrollo. Ya preparamos la base de Django, PostgreSQL y los modelos principales. Nuestro siguiente paso es implementar el juego, sus pantallas y las rutas necesarias. Por ahora, Docker está configurado para hacer pruebas locales.

## 1. Descripción

En nuestro equipo estamos desarrollando **Sonic Memory Card**, un juego de memoria para un solo jugador con una temática visual de Sonic. La idea es sencilla: encontrar todas las parejas de cartas antes de que se agote el tiempo o se alcance el límite de fallos.

Elegimos **Python y Django** para construir la lógica del juego y **PostgreSQL** para guardar la información de usuarios y partidas. Queremos que las jugadas se validen en el servidor: el navegador se encargará de mostrar las cartas y animaciones, mientras Django decidirá si los movimientos son correctos y calculará los resultados.

Además de crear el juego, con este proyecto buscamos poner en práctica lo aprendido en Arquitectura de Computadoras. Para eso trabajaremos con contenedores Docker, redes, volúmenes, Linux, despliegue web y herramientas de administración y monitoreo.

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

## 3. Lo que llevamos desarrollado

Hasta el momento, hemos creado las siguientes partes del proyecto:

- **`PerfilJugador`**: vínculo con el usuario Django, alias y preferencias de audio.
- **`Personaje`**: catálogo de personajes para las cartas, con nombre, origen e imagen.
- **`Partida`**: usuario, dificultad, estado, inicio, límite de tiempo, duración, errores, movimientos, puntuación y estado JSON.
- **`Movimiento`**: número de secuencia, tipo, datos y fecha de cada movimiento.
- Restricción de base de datos para impedir **más de una partida `EN_CURSO` por usuario**.
- Restricción para impedir números de movimiento duplicados en una misma partida.
- Modelos registrados en el **panel administrativo de Django**.
- Migración inicial y volumen Docker para persistir los datos de PostgreSQL.

Esta primera etapa nos permite organizar la información del juego. **Todavía nos falta conectar los modelos con las vistas y la interfaz**, así que por ahora no tenemos partidas jugables.

## 4. Cómo funcionará nuestro juego

Para desarrollar el Proyecto 1 seguiremos las reglas de la guía del catedrático. En cada turno el jugador podrá voltear dos cartas. Si son iguales, la pareja quedará descubierta; si son distintas, se sumará un fallo y volverán a ocultarse.

Implementaremos el orden de las cartas en Django para que el navegador no pueda conocer todo el tablero antes de jugar. También impediremos voltear dos veces la misma carta, seleccionar una carta ya emparejada o descubrir una tercera carta dentro del mismo turno.

### Niveles que implementaremos

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

Nos basaremos en la fórmula de la guía para calcular el puntaje de las partidas ganadas:

```text
Puntaje = (1000 + 5 × segundos_restantes − 25 × fallos) × multiplicador
Puntaje mínimo si gana = 100 × multiplicador
Puntaje si pierde, abandona o agota el tiempo = 0
```

Haremos que Django calcule y guarde el puntaje **una sola vez**. Si el jugador recarga la página, la partida conservará su tiempo real; cuando termine, ya no se podrán realizar movimientos. También respetaremos la tolerancia de **2 segundos** por latencia indicada en la guía.

## 5. Cómo ejecutar nuestro proyecto en una computadora

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

Por ahora, con esta instalación podemos revisar el panel administrativo y comprobar los modelos y la conexión con PostgreSQL. **El juego de cartas todavía está en desarrollo.**

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

Todavía debemos escribir las pruebas automáticas del juego. El comando ya está disponible para ejecutarlas cuando las agreguemos.

## 7. Cómo organizamos los archivos

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

## 8. Arquitectura que estamos construyendo

**Así funciona nuestra configuración local actual:**

```text
Navegador -> localhost:8000 -> Django runserver (web)
                                   |
                                   v
                            PostgreSQL (db)
                                   |
                                   v
                         volumen postgres_data
```

**Así planeamos organizar los servicios para la versión pública:**

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

Cuando preparemos el despliegue, configuraremos el proxy para que sea el único servicio que publique puertos. Mantendremos PostgreSQL en una red interna e incorporaremos el almacenamiento de archivos estáticos, verificaciones de salud y límites de CPU y memoria.

En este momento, `docker-compose.yml` ejecuta `python manage.py runserver` y publica el puerto 8000. **Eso nos sirve para desarrollo local, pero tendremos que cambiarlo antes de publicar el juego en internet.**

## 9. Rutas que nos falta desarrollar

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

De momento, la única ruta que tenemos registrada es **`/admin/`**. Iremos agregando las demás conforme desarrollemos el juego.

## 10. Lo que nos falta completar

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

## 11. Cómo administraremos el proyecto al publicarlo

Cuando terminemos la versión local, prepararemos el despliegue en un servidor Linux. **Los siguientes comandos son parte del procedimiento que debemos implementar y probar**; todavía no funcionan todos con nuestra configuración actual.

En el servidor utilizaremos comandos como estos para levantar los servicios y preparar la aplicación:

```bash
docker compose build web
docker compose up -d
docker compose ps
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check --deploy
```

Para revisar el funcionamiento de los contenedores utilizaremos:

```bash
docker compose logs -f web
docker compose logs proxy
docker stats --no-stream
docker network ls
docker volume ls
```

Para reiniciar y actualizar nuestra aplicación sin borrar los datos usaremos:

```bash
docker compose restart web
git pull
docker compose build web
docker compose up -d web
docker compose exec web python manage.py migrate
```

Para respaldar PostgreSQL usaremos `pg_dump`, y para recuperar la información, `pg_restore`. Primero practicaremos con datos de prueba y guardaremos una copia del respaldo fuera del servidor. Así podremos comprobar que los usuarios y las partidas se conservan incluso después de un problema o una actualización.

## 12. Guía que utilizamos

Para organizar nuestro trabajo tomamos como referencia la **Guía General del Proyecto Final de Arquitectura de Computadoras de la UTH**, especialmente estas partes:

- Sección 4: tecnologías, funcionalidades, estados, puntuación y rutas comunes.
- Sección 5.1: ficha del **Proyecto 1, Memory Game**.
- Secciones 6 y 7: infraestructura, despliegue, administración y recuperación.
- Sección 8: pruebas comunes y automatizadas.
- Secciones 10 a 14: revisiones, entregables, rúbrica y lista de verificación.

### Sobre la temática y los recursos

Elegimos a Sonic como temática visual para nuestro juego. **Este es un proyecto universitario desarrollado por nuestro equipo, no un juego oficial de SEGA.** En `CREDITOS.md` indicaremos de dónde provienen las imágenes, la música y los sonidos que utilicemos, así como sus permisos o licencias de uso.
