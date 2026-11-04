# Créditos de recursos — Sonic Memory Card

Somos el Grupo 1 de la asignatura Arquitectura de Computadoras de la Universidad Tecnológica de Honduras (UTH). Estamos desarrollando **Sonic Memory Card**, nuestro Proyecto 1 (Memory Game), con una temática inspirada en *Sonic the Hedgehog*.

En este documento registramos los recursos que hemos reunido para el juego y sus fuentes. Diferenciamos los materiales que estamos evaluando de los que ya incorporamos. Actualizaremos los créditos cuando confirmemos la procedencia exacta de cada archivo.

## 1. Imágenes de personajes

Para nuestras cartas reunimos imágenes de personajes del universo de Sonic. Consultamos publicaciones de SEGA y estas páginas compartidas durante el desarrollo:

- **Amy Rose:** [Meshy — Amyrose](https://www.meshy.ai/es/tags/amyrose).
- **Ilustraciones y referencias de artistas:** [DeviantArt — referencia compartida](https://www.deviantart.com/morelikethis/Detexki99/887111286).
- **Blaze the Cat:** [Wikijuegos — Blaze the Cat](https://videojuegos.fandom.com/es/wiki/Blaze_the_Cat).
- **Otros personajes:** artículos y galerías de *Sonic* en Fandom. Como punto de partida utilizamos la misma estructura de dirección que la página de Blaze, sustituyendo el nombre del personaje; debemos comprobar que cada página exista y, especialmente, que contenga la imagen exacta utilizada.

### Personajes de nuestro mazo

| Archivo | Personaje | Procedencia por comprobar |
|---|---|---|
| `amy.png` | Amy Rose | Meshy y/o publicación original de la imagen |
| `belle.png` | Belle | Página y autor de la ilustración |
| `blaze.png` | Blaze the Cat | Fandom: enlace de Blaze indicado arriba |
| `eggman.png` | Doctor Eggman | Página y autor de la ilustración |
| `jewel.png` | Jewel | Página y autor de la ilustración |
| `kit.png` | Kit | Página y autor de la ilustración |
| `knuckles.png` | Knuckles | Página y autor de la ilustración |
| `lanolin.png` | Lanolin | Página y autor de la ilustración |
| `metal-sonic.png` | Metal Sonic | Página y autor de la ilustración |
| `mimic.png` | Mimic | Página y autor de la ilustración |
| `rouge.png` | Rouge | Página y autor de la ilustración |
| `shadow.png` | Shadow | Página y autor de la ilustración |
| `silver.png` | Silver | Página y autor de la ilustración |
| `sonic.png` | Sonic the Hedgehog | Artículo de Sonic en Fandom u origen de la imagen |
| `surge.png` | Surge | Página y autor de la ilustración |
| `tails.png` | Tails | Página y autor de la ilustración |
| `tangle.png` | Tangle | Página y autor de la ilustración |
| `whisper.png` | Whisper | Página y autor de la ilustración |

**Nota:** las páginas de Meshy, DeviantArt y Fandom sirven para identificar las fuentes consultadas; no hemos confirmado que cada ilustración de los archivos anteriores proceda exactamente de esas páginas. También debemos distinguir el propietario del personaje del autor de una ilustración concreta. Estar publicada en internet no significa que una imagen tenga autorización para redistribuirse en nuestro juego.

## 2. Música seleccionada

Queremos que la ambientación cambie con el desarrollo de la partida: música tranquila en el menú, música energética mientras jugamos y una alerta cuando se agota el tiempo.

| Momento | Canción | Videojuego | Fuente de referencia | Estado |
|---|---|---|---|---|
| Menú principal | Chao Garden Extended Mix | Sonic Adventure 2 | [Catálogo oficial de SEGA](https://sst.sega.jp/catalog/s065.html) | **Seleccionada para nuestro proyecto académico sin fines comerciales.** |
| Durante la partida | Lights, Camera, Action! (Studiopolis Zone Act 1) | Sonic Mania | [Video de referencia](https://www.youtube.com/watch?v=NIWyZmFSep0) | **Seleccionada para nuestro proyecto académico sin fines comerciales.** |
| Últimos 15 segundos | Drowning Theme | Sonic the Hedgehog (1991) | Archivo de referencia `sonic-1-music-drownings.mp3` | **Seleccionada para nuestro proyecto académico sin fines comerciales.** |

La música de la partida sonará a velocidad normal y, cuando queden **30 segundos**, aumentará progresivamente su ritmo. A los **15 segundos** cambiará a la alerta de ahogamiento. Al ganar o perder, reproduciremos el efecto correspondiente.

Estas canciones forman parte de nuestra selección musical para el proyecto académico, que no tiene fines comerciales. Las canciones y grabaciones originales pertenecen a sus respectivos titulares de derechos; el carácter académico del proyecto no concede por sí solo permisos de distribución.

## 3. Efectos de sonido

### ROHHSA — NETCROSIS VOLUME ONE

- **Creador:** ROHHSA.
- **Paquete:** NETCROSIS VOLUME ONE.
- **Fuente:** https://payhip.com/rohhsa
- **Uso previsto:** sonidos al voltear cartas, acertar, fallar y navegar por el juego.
- **Crédito:** opcional según el `README.txt` incluido en el paquete, pero decidimos mencionar a su creador.

### Chequered Ink — 400 Sounds Pack

- **Creador:** Chequered Ink.
- **Paquete:** 400 Sounds Pack.
- **Fuente:** https://ci.itch.io/400-sounds-pack
- **Uso previsto:** efectos de interfaz, cartas y resultados.
- **Estado:** paquete en evaluación; registraremos los archivos definitivos y sus condiciones cuando los seleccionemos.

### JDSherbert — Recursos por confirmar

Disponemos de un documento de licencia de JDSherbert, aunque todavía debemos identificar si incorporaremos alguno de sus sonidos.

- **Crédito exigido si utilizamos sus recursos:** Sounds by JDSherbert — https://jdsherbert.itch.io
- **Condición importante:** no redistribuir los archivos originales como paquete independiente.

La licencia de JDSherbert no se aplica a las canciones de SEGA ni a los sonidos creados por ROHHSA o Chequered Ink.

## 4. Uso académico y actualización de créditos

Desarrollamos Sonic Memory Card como proyecto académico de la UTH, sin intención de comercializarlo. Reconocemos que *Sonic the Hedgehog*, sus personajes, música y otros elementos originales pertenecen a sus titulares de derechos.

Registraremos para cada recurso su **nombre, autor o titular, URL de origen, condiciones de uso y modificaciones realizadas**. Mantendremos este archivo actualizado junto con nuestro `README.md`.
