from django.core.management.base import BaseCommand

from memory.models import Personaje


class Command(BaseCommand):
    help = "Carga el catálogo inicial de personajes del Memory Game"

    def handle(self, *args, **options):
        personajes = [
            {
                "clave": "sonic",
                "nombre": "Sonic",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Erizo azul conocido por su enorme velocidad y espíritu aventurero.",
                "frase": "Siempre listo para una nueva aventura.",
                "imagen": "memory/images/personajes/sonic.png",
            },
            {
                "clave": "tails",
                "nombre": "Tails",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Zorro de dos colas, piloto e inventor con gran habilidad tecnológica.",
                "frase": "La inteligencia también puede salvar el día.",
                "imagen": "memory/images/personajes/tails.png",
            },
            {
                "clave": "knuckles",
                "nombre": "Knuckles",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Guardián de la Master Emerald y poderoso luchador.",
                "frase": "Fuerza y responsabilidad.",
                "imagen": "memory/images/personajes/knuckles.png",
            },
            {
                "clave": "amy",
                "nombre": "Amy",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Aventurera decidida reconocida por utilizar su gran martillo.",
                "frase": "Determinación ante cualquier desafío.",
                "imagen": "memory/images/personajes/amy.png",
            },
            {
                "clave": "shadow",
                "nombre": "Shadow",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Misterioso erizo con grandes capacidades y poderes relacionados con el Chaos.",
                "frase": "Poder, velocidad y determinación.",
                "imagen": "memory/images/personajes/shadow.png",
            },
            {
                "clave": "eggman",
                "nombre": "Dr. Eggman",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Científico brillante especializado en robots y grandes máquinas.",
                "frase": "Una mente capaz de construir casi cualquier cosa.",
                "imagen": "memory/images/personajes/eggman.png",
            },
            {
                "clave": "rouge",
                "nombre": "Rouge",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Cazadora de tesoros y experta en infiltración.",
                "frase": "Los secretos siempre tienen valor.",
                "imagen": "memory/images/personajes/rouge.png",
            },
            {
                "clave": "blaze",
                "nombre": "Blaze",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Princesa proveniente de otra dimensión con dominio sobre el fuego.",
                "frase": "Control y poder en equilibrio.",
                "imagen": "memory/images/personajes/blaze.png",
            },
            {
                "clave": "silver",
                "nombre": "Silver",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Erizo proveniente del futuro con habilidades psicoquinéticas.",
                "frase": "El futuro todavía puede cambiar.",
                "imagen": "memory/images/personajes/silver.png",
            },
            {
                "clave": "metal-sonic",
                "nombre": "Metal Sonic",
                "origen": Personaje.Origen.VIDEOJUEGO,
                "descripcion": "Rival robótico diseñado para competir contra la velocidad de Sonic.",
                "frase": "Velocidad convertida en tecnología.",
                "imagen": "memory/images/personajes/metal-sonic.png",
            },
            {
                "clave": "tangle",
                "nombre": "Tangle",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Aventurera enérgica que utiliza su larga cola para desplazarse y combatir.",
                "frase": "Una aventura siempre puede volverse más emocionante.",
                "imagen": "memory/images/personajes/tangle.png",
            },
            {
                "clave": "whisper",
                "nombre": "Whisper",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Luchadora reservada que trabaja junto a Wisps y utiliza un Wispon.",
                "frase": "No hace falta hablar mucho para actuar.",
                "imagen": "memory/images/personajes/whisper.png",
            },
            {
                "clave": "surge",
                "nombre": "Surge",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Poderosa rival con capacidades eléctricas y gran velocidad.",
                "frase": "Energía difícil de contener.",
                "imagen": "memory/images/personajes/surge.png",
            },
            {
                "clave": "kit",
                "nombre": "Kit",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Compañero de Surge con habilidades relacionadas con el control del agua.",
                "frase": "El agua puede ser más poderosa de lo que parece.",
                "imagen": "memory/images/personajes/kit.png",
            },
            {
                "clave": "belle",
                "nombre": "Belle",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Robot de madera de personalidad amable y curiosa.",
                "frase": "Comprender el mundo también es una aventura.",
                "imagen": "memory/images/personajes/belle.png",
            },
            {
                "clave": "lanolin",
                "nombre": "Lanolin",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Integrante de la Restoration con una personalidad disciplinada y estratégica.",
                "frase": "Un buen plan puede cambiar una batalla.",
                "imagen": "memory/images/personajes/lanolin.png",
            },
            {
                "clave": "mimic",
                "nombre": "Mimic",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Peligroso cambiaformas especializado en engaño e infiltración.",
                "frase": "Las apariencias pueden engañar.",
                "imagen": "memory/images/personajes/mimic.png",
            },
            {
                "clave": "jewel",
                "nombre": "Jewel",
                "origen": Personaje.Origen.COMIC,
                "descripcion": "Organizadora y administradora vinculada a la Restoration.",
                "frase": "La organización también mantiene a los héroes en marcha.",
                "imagen": "memory/images/personajes/jewel.png",
            },
        ]

        creados = 0
        actualizados = 0

        for datos in personajes:
            _, creado = Personaje.objects.update_or_create(
                clave=datos["clave"],
                defaults={
                    "nombre": datos["nombre"],
                    "origen": datos["origen"],
                    "descripcion": datos["descripcion"],
                    "frase": datos["frase"],
                    "imagen": datos["imagen"],
                    "activo": True,
                },
            )

            if creado:
                creados += 1
            else:
                actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Personajes listos. Creados: {creados}. "
                f"Actualizados: {actualizados}."
            )
        )