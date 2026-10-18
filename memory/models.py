import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilJugador(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil"
    )

    alias = models.CharField(
        max_length=50,
        blank=True
    )

    volumen_musica = models.PositiveSmallIntegerField(
        default=70,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    volumen_efectos = models.PositiveSmallIntegerField(
        default=80,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    silenciado = models.BooleanField(default=False)

    def __str__(self):
        return self.alias or self.usuario.username


class Personaje(models.Model):

    class Origen(models.TextChoices):
        VIDEOJUEGO = "VIDEOJUEGO", "Videojuego"
        COMIC = "COMIC", "Cómic"

    clave = models.SlugField(
        max_length=50,
        unique=True
    )

    nombre = models.CharField(
        max_length=100
    )

    origen = models.CharField(
        max_length=20,
        choices=Origen.choices
    )

    descripcion = models.TextField()

    frase = models.CharField(
        max_length=255,
        blank=True
    )

    imagen = models.CharField(
        max_length=255,
        blank=True
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Partida(models.Model):

    class Dificultad(models.TextChoices):
        FACIL = "FACIL", "Fácil"
        NORMAL = "NORMAL", "Normal"
        DIFICIL = "DIFICIL", "Difícil"

    class Estado(models.TextChoices):
        EN_CURSO = "EN_CURSO", "En curso"
        GANADA = "GANADA", "Ganada"
        PERDIDA = "PERDIDA", "Perdida"
        TIEMPO_AGOTADO = "TIEMPO_AGOTADO", "Tiempo agotado"
        ABANDONADA = "ABANDONADA", "Abandonada"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="partidas"
    )

    dificultad = models.CharField(
        max_length=10,
        choices=Dificultad.choices
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.EN_CURSO
    )

    inicio_servidor = models.DateTimeField(auto_now_add=True)

    limite_segundos = models.PositiveIntegerField()

    fin_servidor = models.DateTimeField(
        null=True,
        blank=True
    )

    duracion_segundos = models.PositiveIntegerField(default=0)

    puntaje = models.IntegerField(default=0)

    errores = models.PositiveIntegerField(default=0)

    movimientos = models.PositiveIntegerField(default=0)

    estado_juego = models.JSONField(default=dict)

    semilla = models.BigIntegerField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-inicio_servidor"]

        constraints = [
            models.UniqueConstraint(
                fields=["usuario"],
                condition=Q(estado="EN_CURSO"),
                name="una_partida_en_curso_por_usuario"
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "dificultad",
                    "estado",
                    "puntaje"
                ]
            )
        ]

    def __str__(self):
        return (
            f"{self.usuario.username} - "
            f"{self.dificultad} - "
            f"{self.estado}"
        )


class Movimiento(models.Model):

    partida = models.ForeignKey(
        Partida,
        on_delete=models.CASCADE,
        related_name="lista_movimientos"
    )

    numero = models.PositiveIntegerField()

    tipo = models.CharField(max_length=50)

    datos = models.JSONField(default=dict)

    creado_en = models.DateTimeField(auto_now_add=True)

    aceptado = models.BooleanField(default=True)

    class Meta:
        ordering = [
            "partida",
            "numero"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "partida",
                    "numero"
                ],
                name="movimiento_unico_por_partida"
            )
        ]

    def __str__(self):
        return (
            f"{self.partida_id} "
            f"- movimiento {self.numero}"
        )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil_jugador(sender, instance, created, **kwargs):
    if created:
        PerfilJugador.objects.get_or_create(
            usuario=instance,
            defaults={
                "alias": instance.username
            }
        )