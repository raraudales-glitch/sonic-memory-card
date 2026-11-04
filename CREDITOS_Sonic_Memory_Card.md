
# Créditos de recursos — Sonic Memory Card

Somos el Grupo 1 de la asignatura Arquitectura de Computadoras de la Universidad Tecnológica de Honduras (UTH). Estamos desarrollando Sonic Memory Card, correspondiente al Proyecto 1: Memory Game.

Para las cartas y la ambientación del juego hemos seleccionado imágenes, música y efectos de sonido relacionados con Sonic the Hedgehog, además de recursos de otros creadores.

En este documento reconocemos a los autores y las fuentes de los recursos que hemos utilizado o seleccionado para nuestro proyecto académico.

## 1. Imágenes y personajes

Para desarrollar el diseño de las cartas utilizamos personajes del universo de Sonic the Hedgehog.

Las imágenes se obtuvieron de distintas páginas de recursos gráficos, galerías de artistas y sitios dedicados a Sonic.

### Fuentes de los personajes

| Personaje | Fuente |
|---|---|
| Amy Rose | [Meshy](https://www.meshy.ai/es/tags/amyrose) |
| Belle | Fuente específica pendiente |
| Blaze the Cat | [Wikijuegos](https://videojuegos.fandom.com/es/wiki/Blaze_the_Cat) |
| Dr. Eggman | [Mario & Sonic Wiki](https://mario-sonic-games.fandom.com/wiki/Dr._Eggman) |
| Jewel the Beetle | [Nibroc-Rock](https://www.deviantart.com/nibroc-rock/art/Jewel-the-Beetle-Render-835902994) |
| Kit the Fennec | [JollyLink](https://www.deviantart.com/jollylink/art/Kit-sunami-913006678) |
| Knuckles | [Sonic X Heroes Forever](https://sonic-x-heroes-forever.fandom.com/wiki/Knuckles_the_Echidna) |
| Lanolin | Fuente específica pendiente |
| Metal Sonic | [TheMarioMan56](https://www.deviantart.com/themarioman56/art/Dark-Metal-Sonic-846552094) |
| Mimic the Octopus | [IDW Sonic Wiki](https://idwsonic.fandom.com/wiki/Mimic_the_Octopus) |
| Rouge the Bat | [RougeAndGlaceon](https://www.deviantart.com/rougeandglaceon/art/Rouge-the-bat%27s-wings-are-part-of-her-back.-1044717860) |
| Shadow | [Pinterest](https://www.pinterest.com/andre8924/shadow-gaming/) |
| Silver | [TotallyNotIncina](https://www.deviantart.com/totallynotincina/art/Silver-the-Hedgehog-987103244) |
| Sonic the Hedgehog | [FreePNGImg](https://freepngimg.com/png/82860-sonic-toy-episode-character-fictional-the-hedgehog) |
| Surge | Fuente específica pendiente |
| Tails | [Condoripedia](https://condoripedia-oficial.fandom.com/es/wiki/Miles_%22Tails%22_Prower) |
| Tangle the Lemur | [JCThornton](https://www.deviantart.com/jcthornton/art/%2B3D-Model-Download%2B-Tangle-The-Lemur-824947605) |
| Whisper | Fuente específica pendiente |

### Referencias gráficas adicionales

También consultamos otras publicaciones y galerías para reunir referencias de los personajes.

- https://www.deviantart.com/morelikethis/Detexki99/887111286
- https://sonic-art-assets-dvd.fandom.com/wiki/Sonic_Rivals_2
- https://ru.pinterest.com/pin/450641506477649526/
- https://www.pinterest.com/pin/smilesfps-smilesfps-on-x--755056693793950877/

Reconocemos que Sonic y sus personajes pertenecen a SEGA y sus respectivos titulares de derechos. Las ilustraciones de otros creadores también pueden estar protegidas por derechos de autor.

Las direcciones anteriores identifican nuestras fuentes de referencia y no representan necesariamente permisos de reutilización.

## 2. Música

Para nuestro juego hemos seleccionado canciones de la franquicia Sonic the Hedgehog.

Nuestro objetivo es que la música cambie según la pantalla y el tiempo restante de la partida, creando una experiencia similar a la de los videojuegos clásicos de Sonic.

### Música del menú principal

**Chao Garden Extended Mix**

- Videojuego: Sonic Adventure 2.
- Publicación: SEGA.
- Uso: menú principal, registro, instrucciones y selección de dificultad.
- Fuente: https://sst.sega.jp/catalog/s065.html
- Estado: seleccionada para nuestro proyecto académico sin fines comerciales.

Elegimos esta canción porque tiene un ritmo tranquilo y resulta apropiada para las pantallas donde el jugador todavía no ha comenzado una partida.

### Música durante las partidas

**Lights, Camera, Action!**

- Videojuego: Sonic Mania.
- Zona: Studiopolis Zone Act 1.
- Compositor: Tee Lopes.
- Uso: música principal de las partidas.
- Fuente: https://www.youtube.com/watch?v=NIWyZmFSep0
- Estado: seleccionada para nuestro proyecto académico sin fines comerciales.

Seleccionamos esta canción por su ritmo dinámico, que acompaña la búsqueda de parejas de cartas.

### Música de los últimos 15 segundos

**Sonic Drowning Theme**

- Videojuego: Sonic the Hedgehog.
- Uso: alerta cuando queden 15 segundos.
- Fuente: https://www.myinstants.com/es/instant/sonic-drowning-music-55284/
- Archivo de referencia: sonic-1-music-drownings.mp3
- Estado: seleccionada para nuestro proyecto académico sin fines comerciales.

Elegimos este sonido porque es una de las alertas de tiempo más reconocibles de los videojuegos de Sonic.

### Funcionamiento musical

La música cambiará automáticamente según el estado de la partida.

| Situación | Música |
|---|---|
| Menú principal | Chao Garden Extended Mix |
| Inicio de partida | Lights, Camera, Action! |
| Quedan 30 segundos | Aceleración progresiva de la música |
| Quedan 15 segundos | Sonic Drowning Theme |
| Victoria | Efecto de victoria |
| Derrota | Efecto de derrota |
| Tiempo agotado | Finalización de la alerta y efecto de derrota |

El tiempo oficial será controlado por Django. JavaScript utilizará los segundos restantes enviados por el servidor para gestionar las transiciones de audio.

Estas canciones forman parte de nuestra selección para el proyecto académico sin fines comerciales. Reconocemos que las grabaciones originales pertenecen a sus titulares de derechos y que el uso académico no concede automáticamente derechos de distribución.

## 3. Efectos de sonido

Para complementar las animaciones del juego seleccionamos efectos de sonido de diferentes paquetes.

### ROHHSA — NETCROSIS VOLUME ONE

- Autor: ROHHSA.
- Paquete: NETCROSIS VOLUME ONE.
- Fuente: https://payhip.com/rohhsa
- Uso previsto: sonidos de navegación, interacción con cartas, aciertos y errores.
- Crédito: opcional según la documentación del paquete.

Agradecemos a ROHHSA por compartir sus efectos de sonido.

### Chequered Ink — 400 Sounds Pack

- Autor: Chequered Ink.
- Paquete: 400 Sounds Pack.
- Fuente: https://ci.itch.io/400-sounds-pack
- Uso previsto: efectos de interfaz, cartas, resultados y notificaciones.
- Estado: estamos seleccionando los sonidos que mejor se adapten al juego.

### JDSherbert

También contamos con una licencia de recursos creada por JDSherbert.

En caso de utilizar sus efectos de sonido, incluiremos el crédito solicitado por el autor:

**Sounds by JDSherbert — https://jdsherbert.itch.io**

Su licencia permite utilizar los recursos dentro de proyectos, pero restringe la redistribución de los archivos originales como un paquete independiente.

## 4. Sobre nuestro proyecto

Sonic Memory Card es nuestro proyecto académico para la asignatura de Arquitectura de Computadoras de la Universidad Tecnológica de Honduras.

Nuestro propósito es desarrollar un juego de memoria utilizando las siguientes tecnologías:

- Python
- Django
- PostgreSQL
- Docker
- HTML
- CSS
- JavaScript

Mediante este proyecto buscamos poner en práctica nuestros conocimientos sobre programación, bases de datos, contenedores, arquitectura de servicios y administración de servidores.

Agradecemos a los creadores de los recursos gráficos y sonoros que hemos seleccionado para desarrollar la identidad visual y auditiva de nuestro juego.

Este documento se actualizará conforme terminemos de incorporar los recursos definitivos.
