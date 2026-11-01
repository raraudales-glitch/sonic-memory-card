# 🦔 Sonic Memory Card

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.x-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)

Un juego de memoria (Memory Card) con temática de Sonic the Hedgehog, desarrollado con Django en el backend, PostgreSQL como base de datos y completamente contenerizado con Docker para un despliegue y desarrollo sencillos y consistentes.

## 🚀 Características

- **Entorno Contenerizado:** Configuración completa con Docker y Docker Compose para eliminar el problema de "funciona en mi máquina".
- **Base de Datos Robusta:** PostgreSQL configurado para manejar los datos del juego (puntajes, usuarios, estado de las partidas).
- **Backend Escalable:** Arquitectura basada en Django, lista para crecer con APIs REST o renderizado de plantillas.
- **Temática Sonic:** Diseño y lógica orientados a los personajes y elementos del universo de Sonic.

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3.x, Django
- **Base de Datos:** PostgreSQL
- **Contenerización:** Docker, Docker Compose
- **Control de Versiones:** Git

## 📋 Prerrequisitos

Antes de comenzar, asegúrate de tener instalados en tu sistema:
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/) (incluido en Docker Desktop para Windows/Mac)
- Git

## ⚙️ Instalación y Configuración

Sigue estos pasos para levantar el entorno de desarrollo localmente:

1. **Clona el repositorio:**
```bash
   git clone https://github.com/raraudales-glitch/sonic-memory-card.git
   cd sonic-memory-card
```

2. **Configura las variables de entorno:**
   Crea un archivo `.env` en la raíz del proyecto basándote en el ejemplo (si existe) o con las siguientes variables básicas:
```env
   DEBUG=True
   SECRET_KEY=tu_clave_secreta_de_django_aqui
   POSTGRES_DB=sonic_db
   POSTGRES_USER=sonic_user
   POSTGRES_PASSWORD=sonic_password
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
```

3. **Construye y levanta los contenedores:**
```bash
   docker-compose up --build -d
```

4. **Aplica las migraciones de Django:**
```bash
   docker-compose exec web python manage.py migrate
```

5. **(Opcional) Crea un superusuario para acceder al panel de administración:**
```bash
   docker-compose exec web python manage.py createsuperuser
```

## 🎮 Uso

Una vez que los contenedores estén en ejecución:

- **Aplicación Web:** Accede a [http://localhost:8000](http://localhost:8000)
- **Panel de Administración de Django:** Accede a [http://localhost:8000/admin](http://localhost:8000/admin)
- **Base de Datos:** PostgreSQL está corriendo en el puerto `5432` (accesible desde otros contenedores como `db:5432`).

Para detener el entorno:
```bash
docker-compose down
```

## 📂 Estructura del Proyecto (Inicial)

```text
sonic-memory-card/
├── docker-compose.yml      # Configuración de los servicios Docker
├── Dockerfile              # Instrucciones para la imagen de Django
├── .env                    # Variables de entorno (no versionar)
├── .gitignore              # Archivos ignorados por Git
├── manage.py               # Script de gestión de Django
└── sonic_memory/           # Directorio principal del proyecto Django
    ├── __init__.py
    ├── settings.py         # Configuración del proyecto
    ├── urls.py             # Enrutamiento principal
    └── wsgi.py / asgi.py
```
*(Nota: La estructura puede variar a medida que se agreguen aplicaciones como `game`, `users`, etc.)*

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si deseas mejorar el juego, agregar nuevas características o corregir errores, por favor abre un *Issue* o envía un *Pull Request*.

1. Haz un Fork del proyecto.
2. Crea una rama para tu función (`git checkout -b feature/NuevaCaracteristica`).
3. Haz commit de tus cambios (`git commit -m 'Agrega nueva característica'`).
4. Haz push a la rama (`git push origin feature/NuevaCaracteristica`).
5. Abre un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---
*Desarrollado con 💙 y anillos por [raraudales-glitch](https://github.com/raraudales-glitch).*
