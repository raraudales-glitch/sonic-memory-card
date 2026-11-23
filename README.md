# Sonic Memory Card

**Proyecto 1: Memory Game (emparejamiento de cartas)**  
**Asignatura:** Arquitectura de Computadoras  
**Carrera:** Ingeniería en Computación  
**Universidad:** Universidad Tecnológica de Honduras (UTH)  
**Repositorio:** https://github.com/raraudales-glitch/sonic-memory-card  
**Juego público:** https://159-54-142-136.sslip.io/

> **Estado del proyecto (noviembre de 2026):** aplicación desarrollada y publicada en Oracle Cloud con Django, PostgreSQL, Gunicorn, Caddy y HTTPS. El juego dispone de usuarios, partidas, resultados, clasificación y TOP 5 semanal. En Oracle se ejecutaron 46 pruebas: **44 aprobadas, 0 fallidas y 2 omitidas** porque las pruebas de navegador requieren Chromium. Continúan pendientes algunas evidencias académicas, una prueba documentada de restauración y mejoras en la animación inicial de previsualización.

## 1. Descripción

**Sonic Memory Card** es un juego de memoria para un jugador por partida, inspirado visualmente en el universo de Sonic the Hedgehog. El objetivo consiste en encontrar todas las parejas antes de que termine el tiempo o se supere el límite de fallos correspondiente a la dificultad elegida.

Desarrollamos el backend con **Python y Django**, mientras que **PostgreSQL** conserva usuarios, perfiles, partidas, movimientos y resultados. El navegador utiliza HTML, CSS y JavaScript para mostrar el tablero, las animaciones y el audio; **Django valida las jugadas y controla las condiciones oficiales de la partida**. La aplicación también ofrece historial personal, estadísticas, clasificación por dificultad y un TOP 5 semanal de victorias oficiales.

Este proyecto nos permite aplicar los contenidos de Arquitectura de Computadoras: virtualización en la nube, Linux, contenedores, redes, volúmenes, límites de recursos, seguridad, pruebas y despliegue de servicios web. Comenzamos con un entorno local y evolucionamos hacia una instalación pública en Oracle Cloud.

**Enlaces de acceso:** [Juego](https://159-54-142-136.sslip.io/) · [Panel de administración](https://159-54-142-136.sslip.io/admin/) · [TOP 5 semanal](https://159-54-142-136.sslip.io/top-semanal/) · [Créditos completos](CREDITOS.md).

## 2. Tecnologías

| Tecnología | Función | Estado actual |
|---|---|---|
| Python 3.12 | Ejecución del backend | Incluido en la imagen Docker de Django |
| Django 5.2 LTS | Aplicación, autenticación, lógica del juego y administración | Implementado y publicado |
| PostgreSQL 16 | Persistencia de usuarios, partidas y puntuaciones | Servicio `db` con volumen persistente |
| Psycopg 3 | Conexión entre Django y PostgreSQL | Utilizado por el backend |
| Docker y Docker Compose | Construcción y ejecución de servicios | Implementados en el proyecto |
| HTML, CSS y JavaScript | Vistas, diseño adaptable, cartas, interacciones y audio | Implementados; con optimizaciones móviles |
| Gunicorn | Servidor WSGI de Django en producción | En uso dentro del servicio `web` |
| Caddy 2 | Proxy inverso, HTTPS y archivos estáticos | En uso dentro del servicio `proxy` |
| Ubuntu Linux 24.04 LTS | Sistema operativo del servidor | En uso en Oracle Cloud |
| Oracle Cloud Infrastructure | Máquina virtual y alojamiento público | Despliegue realizado |
| Git y GitHub | Historial de cambios y repositorio | En uso |
| HTTPS | Comunicación cifrada entre cliente y servidor | Verificado en la URL pública |

La instalación de producción usa los servicios **`web`**, **`db`** y **`proxy`**. El puerto de PostgreSQL no se publica directamente en Internet. Las configuraciones locales pueden diferir de las de Oracle; antes de ejecutar comandos debe verificarse el archivo Compose correspondiente.

## 3. Funcionalidades desarrolladas

### Modelos y persistencia

- **`PerfilJugador`**: relación con el usuario de Django, alias y preferencias de volumen o silencio.
- **`Personaje`**: catálogo de personajes, procedencia, descripción, frases e imagen.
- **`Partida`**: usuario, dificultad, estado, tiempo, duración, errores, movimientos, puntuación y estado del tablero almacenado en JSON.
- **`Movimiento`**: secuencia, tipo de acción, datos asociados, aceptación y fecha de registro.
- Restricción de base de datos para impedir más de una partida `EN_CURSO` por usuario.
- Restricción para impedir la repetición del número de secuencia de un movimiento en una partida.
- Modelos registrados en el panel administrativo de Django.

### Interfaz y reglas

- Registro, inicio y cierre de sesión, con rutas protegidas para los datos privados.
- Pantallas de inicio, instrucciones, selección de dificultad, tablero y resultado.
- Tres niveles: Fácil, Normal y Difícil.
- Validación del volteo de cartas en Django, con protección contra movimientos duplicados.
- Persistencia del historial, estadísticas y puntuaciones oficiales.
- Clasificación histórica TOP 10 por dificultad y TOP 5 semanal global dentro de la base de datos del servidor compartido.
- Interfaz adaptable, controles de ratón y pantalla táctil, efectos de audio y controles de volumen.
- Panel `/admin/` para las operaciones permitidas a superusuarios y cuentas STAFF según sus permisos.

### Ranking semanal y sincronización opcional

El **TOP 5 semanal** del servidor compartido obtiene sus resultados de las victorias oficiales registradas en su PostgreSQL. La semana se interpreta en la zona horaria `America/Tegucigalpa`, de lunes a domingo. El ranking considera los puntos acumulados y los criterios de desempate definidos en el proyecto; las semanas anteriores con resultados quedan disponibles para consulta.

El proyecto también documenta una **sincronización opcional entre instalaciones independientes** mediante `/top-sincronizado/` y un servicio central. No debe confundirse con el TOP 5 del servidor público: **la sincronización central no se considera activa ni verificada en Oracle por el solo hecho de estar documentada**. Su utilización requiere un despliegue y unas credenciales propias.

El sincronizador puede retransmitir resultados locales al servicio central bajo su configuración correspondiente. Un servidor federado que recibe resultados debe confiar en la integridad de las instalaciones participantes: HTTPS, tokens y deduplicación no demuestran por sí solos que cada partida se haya jugado sin manipulación. Para una competición verificable, el servidor central tendría que controlar o verificar las jugadas oficiales.

## 4. Reglas y funcionamiento del juego

En una partida, el jugador selecciona dos cartas por turno. Si contienen el mismo personaje, la pareja permanece descubierta. Si son diferentes, se registra un fallo y ambas vuelven a ocultarse tras el intervalo correspondiente. El servidor valida la posición, la identidad de la partida, el número de secuencia y las condiciones de tiempo y estado.

### Parámetros de los niveles

| Parámetro | Fácil | Normal | Difícil |
|---|---:|---:|---:|
| Tablero | 4 × 4 | 4 × 5 | 6 × 6 |
| Cartas | 16 | 20 | 36 |
| Parejas | 8 | 10 | 18 |
| Tiempo límite | 150 s | 150 s | 210 s |
| Fallos permitidos | 16 | 15 | 22 |
| Vista previa inicial | 3 s | 1,5 s | Sin vista previa |
| Visualización de un fallo | 1,0 s | 0,8 s | 0,6 s |
| Multiplicador | ×1,0 | ×1,5 | ×2,0 |

Estos son los parámetros documentados en el proyecto. Si se modifica `memory/services.py`, la tabla debe revisarse para mantenerla sincronizada con las reglas vigentes.

### Estados posibles

- **EN_CURSO:** permite jugadas válidas.
- **GANADA:** se encontraron todas las parejas dentro de las condiciones oficiales.
- **PERDIDA:** se excedió el límite de fallos.
- **TIEMPO_AGOTADO:** expiró el tiempo controlado por el servidor.
- **ABANDONADA:** el usuario abandonó o inició otra partida según la lógica implementada.

### Cálculo de la puntuación

```text
Puntaje = (1000 + 5 × segundos_restantes − 25 × fallos) × multiplicador
Puntaje mínimo si gana = 100 × multiplicador
Puntaje si pierde, abandona o agota el tiempo = 0
```

El puntaje oficial se calcula y conserva en el servidor. El proyecto contempla una tolerancia de **2 segundos por latencia**, según la guía académica, y evita que recargar la página reinicie el tiempo oficial o que un movimiento repetido otorgue puntos adicionales.

**Observación de usabilidad pendiente:** en pruebas con teléfono y computadora comprobamos una mejora en la fluidez del volteo normal. Sin embargo, la **previsualización inicial de Fácil y Normal aún se percibe brusca** y necesita una transición visual más suave. No se considera resuelta esa mejora estética.

## 5. Instalación y ejecución local

### Requisitos

- Git.
- Docker Desktop con motor Linux activo o Docker Engine con Docker Compose v2.
- Un puerto libre para el acceso local, de acuerdo con el Compose utilizado.
- No hace falta instalar Python ni PostgreSQL directamente en el equipo si se utiliza Docker.

### 5.1. Descarga y configuración en PowerShell (Windows)

**1. Clonar el repositorio (solo si todavía no existe una copia local):**

```powershell
git clone https://github.com/raraudales-glitch/sonic-memory-card.git
cd sonic-memory-card
```

Si ya se dispone de una copia con cambios locales, se debe utilizar esa carpeta en vez de volver a clonar el proyecto.

**2. Preparar variables de entorno privadas:**

```powershell
Copy-Item .env.example .env
notepad .env
```

La configuración requiere, según el entorno, los parámetros `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`, `DJANGO_SECRET_KEY` y `DJANGO_DEBUG`. Para la conexión entre contenedores, normalmente se utiliza `DB_HOST=db` y `DB_PORT=5432`.

No se deben subir credenciales reales, claves ni el archivo `.env` a GitHub. Los nombres y valores de `.env.example` deben revisarse contra la versión del Compose que se esté ejecutando.

**3. Comprobar y construir los servicios:**

```powershell
docker compose config --services
docker compose up -d --build
docker compose ps
```

**4. Crear o actualizar las tablas de Django:**

```powershell
docker compose exec web python manage.py migrate
```

**5. Cargar el catálogo inicial de 18 personajes:**

```powershell
docker compose exec web python manage.py cargar_personajes
```

**6. Ejecutar pruebas con una base de pruebas independiente:**

```powershell
docker compose run --rm --no-deps -e DJANGO_DEBUG=False web python manage.py test memory
```

Estas pruebas no deben ejecutarse contra las tablas reales de usuarios o partidas. Django utiliza una base de pruebas independiente siempre que el entorno tenga los permisos y la configuración adecuados.

**7. Consultar la dirección del sitio:**

```powershell
docker compose ps
```

La versión inicial de esta guía usaba `http://localhost:8081/` y `http://localhost:8081/admin/`. **Ese puerto solo será válido si el archivo Compose local lo publica actualmente.** En despliegues con Caddy, se debe utilizar la dirección y el puerto indicados por `docker compose ps`.

### 5.2. Usuarios STAFF y administración

El proyecto dispone del comando `crear_usuarios_iniciales` para preparar cuentas de trabajo según los permisos previstos. Las cuentas documentadas son **Stanley, Nelson, Astrid, Rut, Lester y Gustavo**. Para crear o verificar una cuenta específica en una instalación local:

```powershell
docker compose exec web python manage.py crear_usuarios_iniciales --usuario Stanley
```

La inicialización de todas las cuentas, incluida `ADMIN`, puede realizarse con:

```powershell
docker compose exec web python manage.py crear_usuarios_iniciales
```

Las credenciales deben configurarse de manera privada e interactiva. Las cuentas STAFF están destinadas a la edición autorizada de personajes y a las consultas que permitan sus permisos; no equivalen a un superusuario. Se debe verificar cada permiso en `/admin/` antes de delegar acceso a datos sensibles.

### 5.3. TOP 5 local, compartido y federado

- El TOP 5 de una instalación usa exclusivamente las victorias oficiales de su base PostgreSQL.
- Cuando varias personas juegan en el **mismo servidor Oracle**, comparten la clasificación de esa base.
- `/top-sincronizado/` corresponde a la modalidad opcional entre instalaciones diferentes y requiere un servicio central configurado por separado.
- La modalidad federada descrita en el proyecto utiliza parámetros como `RANKING_CENTRAL`, `RANKING_URL`, `RANKING_CREDENCIALES_CENTRALES` y `RANKING_CREDENCIALES_LOCALES`. Deben revisarse los módulos disponibles y su configuración antes de activarla.
- En instalaciones que dispongan del comando correspondiente, `python manage.py sincronizar_ranking` puede realizar la transmisión puntual; la ejecución continua exige un proceso administrado aparte.

Los tokens y las credenciales del ranking se almacenan exclusivamente en una configuración privada. No se comparten en el README. **No es necesario activar esta sincronización para que funcione el TOP 5 semanal del servidor público.**

## 6. Comandos de administración

Estos comandos se ejecutan **desde la carpeta del proyecto**. En Windows con Docker Desktop, normalmente no se utiliza `sudo`; en Ubuntu de Oracle hemos utilizado `sudo docker compose`.

| Acción | Comando |
|---|---|
| Ver servicios | `docker compose ps` |
| Construir la imagen web | `docker compose build web` |
| Iniciar servicios | `docker compose up -d` |
| Revisar configuración | `docker compose config` |
| Registros de Django | `docker compose logs --tail=100 web` |
| Registros del proxy | `docker compose logs --tail=100 proxy` |
| Registros de PostgreSQL | `docker compose logs --tail=100 db` |
| Consumo de recursos | `docker stats --no-stream` |
| Migraciones | `docker compose exec web python manage.py migrate` |
| Comprobación de Django | `docker compose exec web python manage.py check` |
| Archivos estáticos | `docker compose exec web python manage.py collectstatic --noinput` |
| Pruebas | `docker compose run --rm --no-deps -e DJANGO_DEBUG=False web python manage.py test memory` |
| Detener sin eliminar volúmenes | `docker compose down` |

**Precaución:** `docker compose down -v` puede eliminar los volúmenes de la base de datos y provocar la pérdida de usuarios, partidas y puntuaciones. No debe utilizarse para reiniciar el juego o publicar una actualización.

En la ejecución comprobada de noviembre de 2026, el resultado de las pruebas en Oracle fue **`Ran 46 tests` y `OK (skipped=2)`**: 44 aprobadas y dos omitidas por falta de Chromium para las pruebas de navegador y pantalla táctil. Esto no sustituye una revisión manual de las animaciones en un teléfono real.

## 7. Organización de archivos

```text
sonic-memory-card/
├── config/
│   ├── settings.py
│   └── urls.py
├── memory/
│   ├── admin.py
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   ├── migrations/
│   ├── management/commands/
│   ├── templates/memory/
│   ├── static/memory/
│   │   ├── images/
│   │   ├── js/
│   │   │   └── tablero.js
│   │   └── audio/
│   ├── test_auditoria_partidas.py
│   ├── test_rutas_obligatorias.py
│   └── test_tablero_tactil.py
├── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── requirements.txt
├── manage.py
├── .env.example
├── .gitignore
├── CREDITOS.md
└── README.md
```

Este es un **resumen de los archivos relevantes**, no un inventario exhaustivo del repositorio. La disponibilidad de configuraciones alternativas de ranking y archivos específicos de producción depende de cada instalación. El archivo `.env` real se mantiene fuera del control de versiones.

## 8. Arquitectura de producción en Oracle Cloud

La aplicación está publicada en una máquina virtual con Ubuntu Linux. Docker Compose administra tres contenedores separados:

```text
Jugador (navegador o teléfono)
             |
             | HTTPS (443)
             v
        Caddy 2 (proxy)
             |
             | Red frontend
             v
      Gunicorn + Django (web)
             |
             | Red backend privada
             v
        PostgreSQL 16 (db)
             |
             v
    Volumen persistente de datos
```

El servicio **`proxy`** recibe HTTPS y sirve archivos estáticos; **`web`** ejecuta Django con Gunicorn; **`db`** guarda los datos persistentes. PostgreSQL escucha internamente en su red de contenedores, sin publicar el puerto `5432` al exterior.

En nuestra comprobación de Oracle, `docker compose ps` mostró los tres servicios iniciados y PostgreSQL con estado saludable. El acceso a `https://159-54-142-136.sslip.io/` respondió por HTTPS y redirigió al inicio de sesión cuando correspondía. Se utilizaron configuraciones de producción específicas para HTTPS, redes y límites de recursos.

La instalación inicial en Windows utilizaba `runserver` para comenzar a trabajar. **La versión pública no utiliza `runserver`: utiliza Gunicorn detrás de Caddy.** Esta distinción es importante para comprender la evolución del proyecto y evitar instrucciones contradictorias.

## 9. Rutas y servicios

Las rutas previstas en la guía y documentadas por el proyecto son las siguientes. La disponibilidad de los alias de cuentas debe comprobarse contra `config/urls.py` en el commit desplegado.

| Método y ruta | Función |
|---|---|
| `GET /` | Inicio del juego |
| `GET, POST /cuentas/registro/` | Registro de usuario |
| `GET, POST /cuentas/login/` | Inicio de sesión (ruta documentada; verificar alias vigente) |
| `POST /cuentas/logout/` | Cierre de sesión |
| `GET /instrucciones/` | Reglas del juego |
| `GET /jugar/` | Selección de dificultad |
| `POST /partidas/nueva/` | Crear partida |
| `GET /partidas/<uuid>/` | Tablero de una partida |
| `GET /api/partidas/<uuid>/estado/` | Estado y tiempo restante |
| `POST /api/partidas/<uuid>/accion/` | Voltear carta con número de secuencia |
| `POST /api/partidas/<uuid>/abandonar/` | Abandonar partida |
| `GET /partidas/<uuid>/resultado/` | Resultado final |
| `GET /perfil/` | Perfil y estadísticas |
| `GET /historial/` | Partidas anteriores del usuario |
| `GET /clasificacion/?nivel=facil` | Clasificación histórica TOP 10 por dificultad (también `normal` y `dificil`) |
| `GET /top-semanal/` | TOP 5 semanal del servidor |
| `GET /top-sincronizado/` | Clasificación federada opcional, si se configura |
| `GET /salud/` | Estado de la aplicación y la base de datos |
| `GET /admin/` | Panel administrativo de Django |

Durante la verificación pública observamos una redirección a **`/accounts/login/?next=/`** desde la página principal. Debe comprobarse la relación entre ese destino real y la ruta `/cuentas/login/` indicada en la guía antes de declarar que ambos caminos son equivalentes.

La API de volteo recibe `posicion` y `seq_num` en JSON. La API verifica sesión, pertenencia de la partida, protección CSRF y la secuencia idempotente de movimientos. `/salud/` devuelve HTTP 200 cuando la base de datos responde y HTTP 503 si falla la comprobación; no expone los detalles internos del error.

## 10. Estado de avance y actividades pendientes

### Juego y usuarios

- [x] Registro, inicio y cierre de sesión; privacidad entre usuarios.
- [x] Pantallas de inicio, instrucciones, selección de nivel y resultados.
- [x] Interfaz adaptable y controles de ratón y pantalla táctil.
- [x] Generar y barajar cartas desde Django sin publicar el orden completo.
- [x] Validar posiciones, movimientos repetidos y tiempo del servidor.
- [x] Implementar los tres niveles y sus condiciones de finalización.
- [x] Calcular puntuación oficial y registrar resultados en PostgreSQL.
- [x] Historial, estadísticas, clasificación por dificultad y TOP 5 semanal.
- [x] Incorporar música, efectos, animaciones y controles de volumen.
- [x] Documentar recursos gráficos y sonoros en `CREDITOS.md`.
- [x] Optimizar imágenes y respuesta táctil del tablero.
- [ ] Mejorar la suavidad de la previsualización inicial de Fácil y Normal.
- [ ] Verificar visualmente con Chromium las dos pruebas de interacción omitidas en el contenedor.

### Infraestructura y publicación

- [x] Ejecutar Django con Gunicorn bajo un usuario sin privilegios.
- [x] Incorporar Caddy, redes `frontend` y `backend`, archivos estáticos y comprobaciones de salud.
- [x] Establecer límites de memoria y CPU de los servicios.
- [x] Configurar producción con `DJANGO_DEBUG=False`, hosts y orígenes CSRF permitidos.
- [x] Publicar en Oracle Cloud con Ubuntu Linux, SSH y HTTPS.
- [x] Comprobar conexión externa y aislamiento del puerto de PostgreSQL.
- [x] Construir y publicar actualizaciones del contenedor web sin borrar volúmenes de la base.
- [x] Crear un respaldo de PostgreSQL y comprobar que el archivo de respaldo es legible.
- [ ] Demostrar y documentar una restauración real del respaldo en un entorno separado.
- [ ] Conservar una copia externa verificada del respaldo, si aún no se ha realizado.

### Calidad, evidencias y entregables

- [x] Incorporar más de 10 pruebas automatizadas.
- [x] Ejecutar 46 pruebas en Oracle: 44 aprobadas, 0 fallos y 2 omitidas.
- [x] Verificar las protecciones HTTPS, CSRF, autenticación e idempotencia mediante pruebas automatizadas.
- [x] Documentar la URL pública del videojuego.
- [ ] Completar y organizar todas las evidencias requeridas de M1–M6 y C01–C17.
- [ ] Consolidar evidencias de CPU, memoria, disco, kernel, redes, volúmenes y `docker stats`.
- [ ] Documentar la prueba de carga moderada y un fallo controlado.
- [ ] Demostrar la restauración desde un respaldo sin afectar datos reales.
- [ ] Revisar y entregar el informe técnico final y la bitácora de uso de IA.
- [ ] Completar la presentación final y la defensa grupal.
- [ ] Revisar la participación y los commits de todos los integrantes.
- [ ] Documentar una cuenta de prueba si se necesita, sin publicar contraseñas privadas.
- [ ] Verificar licencias o permisos de los recursos externos pendientes.

## 11. Administración y actualizaciones de Oracle Cloud

Los siguientes comandos corresponden al servidor **Ubuntu de Oracle**, dentro del directorio `~/sonic-memory-card`. No deben ejecutarse en PowerShell de Windows. Los archivos `.env`, `Caddyfile`, `config/settings.py` y `docker-compose.yml` pueden contener ajustes propios de producción y no deben sobrescribirse sin revisión.

### Revisar el estado del servidor

```bash
cd ~/sonic-memory-card
git status --short
sudo docker compose ps
sudo docker stats --no-stream
sudo docker compose logs --tail=50 web
```

### Revisar y descargar una actualización sin perder configuraciones

```bash
cd ~/sonic-memory-card
git fetch origin main
git --no-pager diff --name-only HEAD origin/main
```

Solo si los cambios entrantes **no entran en conflicto con los archivos modificados del servidor** y se ha comprobado su contenido, se puede continuar:

```bash
git pull --ff-only origin main
sudo docker compose build web
sudo docker compose run --rm --no-deps -e DJANGO_DEBUG=False web python manage.py test memory
```

Si las pruebas terminan correctamente y se ha planificado la publicación:

```bash
sudo docker compose up -d --no-deps web
sudo docker compose exec web python manage.py collectstatic --noinput
sudo docker compose ps
curl -IL --max-time 20 https://159-54-142-136.sslip.io/
```

Cuando una actualización incluye cambios de base de datos, primero deben revisarse las migraciones y realizar una copia de seguridad. Se debe coordinar la actualización de archivos estáticos para evitar que el navegador mezcle versiones del JavaScript durante el despliegue.

### Respaldo y recuperación

La base de datos utiliza un volumen persistente. **No utilizar `docker compose down -v`** para reiniciar o actualizar. La creación de un respaldo con `pg_dump` es un paso distinto de la **restauración verificada con `pg_restore`**: esta última sigue pendiente de una prueba documentada en una base aislada. Las copias deben protegerse y, preferiblemente, almacenarse también fuera del servidor.

### Seguimiento y comprobación

Para revisar contenedores, redes, volúmenes y consumo de recursos se pueden utilizar `sudo docker compose ps`, `sudo docker network ls`, `sudo docker volume ls`, `sudo docker stats --no-stream` y los registros de cada servicio. El resultado de estas verificaciones debe conservarse como evidencia técnica de la entrega.

## 12. Guía del proyecto y créditos de recursos

### Referencia académica

El desarrollo se basa en la **Guía General del Proyecto Final de Arquitectura de Computadoras de la UTH**, principalmente en las secciones sobre tecnologías, Memory Game, infraestructura, pruebas, entregables y evaluación.

### Créditos y atribuciones

Sonic Memory Card es un proyecto académico **no oficial** inspirado en el universo de Sonic the Hedgehog. Reconocemos a SEGA y a los demás titulares de los personajes, juegos y composiciones. La referencia a un artista o una plataforma no equivale automáticamente a autorización o licencia para redistribuir su obra. Los enlaces siguientes corresponden a las fuentes **registradas en nuestro documento original de créditos**, no necesariamente a la autoría definitiva de cada archivo usado.

#### Música

| Uso documentado | Música | Videojuego / autor identificado | Fuente o referencia |
|---|---|---|---|
| Menús | Chao Garden Extended Mix | Sonic Adventure 2 / publicación de SEGA | [Referencia en YouTube](https://www.youtube.com/watch?v=_Uznh4WfOPg) · [Catálogo de SEGA](https://sst.sega.jp/catalog/s065.html) |
| Durante las partidas | Lights, Camera, Action! | Sonic Mania, Studiopolis Zone Act 1 / Tee Lopes | [Referencia en YouTube](https://www.youtube.com/watch?v=NIWyZmFSep0) |
| Últimos 15 segundos | Sonic Drowning Theme | Sonic the Hedgehog (1991) | [Referencia de audio](https://www.myinstants.com/es/instant/sonic-drowning-music-55284/) |

#### Imágenes y personajes

| N.º | Personaje | Fuente o publicación registrada |
|---:|---|---|
| 1 | Amy Rose | [Meshy — Amy Rose](https://www.meshy.ai/es/tags/amyrose) |
| 2 | Belle the Tinkerer | [Pinterest — referencia proporcionada](https://www.pinterest.com/ideas/tiara-the-manx/912357057396/) |
| 3 | Blaze the Cat | [Wiki de Videojuegos — Blaze](https://videojuegos.fandom.com/es/wiki/Blaze_the_Cat) |
| 4 | Dr. Eggman | [Mario & Sonic Games Wiki](https://mario-sonic-games.fandom.com/wiki/Dr._Eggman) |
| 5 | Jewel the Beetle | [Nibroc-Rock — DeviantArt](https://www.deviantart.com/nibroc-rock/art/Jewel-the-Beetle-Render-835902994) |
| 6 | Kit the Fennec | [JollyLink — DeviantArt](https://www.deviantart.com/jollylink/art/Kit-sunami-913006678) |
| 7 | Knuckles the Echidna | [Sonic X Heroes Forever Wiki](https://sonic-x-heroes-forever.fandom.com/wiki/Knuckles_the_Echidna) |
| 8 | Lanolin the Sheep | [theEyZmaster — Newgrounds](https://www.newgrounds.com/art/view/theeyzmaster/sonic-lanolin) |
| 9 | Metal Sonic | [TheMarioMan56 — DeviantArt](https://www.deviantart.com/themarioman56/art/Dark-Metal-Sonic-846552094) |
| 10 | Mimic the Octopus | [IDW Sonic Wiki](https://idwsonic.fandom.com/wiki/Mimic_the_Octopus) |
| 11 | Rouge the Bat | [RougeAndGlaceon — DeviantArt](https://www.deviantart.com/rougeandglaceon/art/Rouge-the-bat%27s-wings-are-part-of-her-back.-1044717860) |
| 12 | Shadow the Hedgehog | [Pinterest — Shadow Gaming](https://www.pinterest.com/andre8924/shadow-gaming/) |
| 13 | Silver the Hedgehog | [TotallyNotIncina — DeviantArt](https://www.deviantart.com/totallynotincina/art/Silver-the-Hedgehog-987103244) |
| 14 | Sonic the Hedgehog | [FreePNGImg — Sonic](https://freepngimg.com/png/82860-sonic-toy-episode-character-fictional-the-hedgehog) |
| 15 | Surge the Tenrec | [DeviantArt — galería de referencia](https://www.deviantart.com/morelikethis/ziomal1987/1321986768?page=4) |
| 16 | Miles «Tails» Prower | [Condoripedia — Tails](https://condoripedia-oficial.fandom.com/es/wiki/Miles_%22Tails%22_Prower) |
| 17 | Tangle the Lemur | [JCThornton — DeviantArt](https://www.deviantart.com/jcthornton/art/%2B3D-Model-Download%2B-Tangle-The-Lemur-824947605) |
| 18 | Whisper the Wolf | [Pinterest — smilesfps](https://www.pinterest.com/pin/smilesfps-smilesfps-on-x--755056693793950877/) |

**Documento detallado:** [CREDITOS.md — fuentes, autores, referencias y condiciones](CREDITOS.md).

---

**Universidad Tecnológica de Honduras · Arquitectura de Computadoras · Proyecto Sonic Memory Card**
