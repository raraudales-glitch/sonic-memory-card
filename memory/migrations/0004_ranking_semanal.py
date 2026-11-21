import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("memory", "0003_practica_sin_puntaje")]

    operations = [
        migrations.CreateModel(
            name="ResultadoRanking",
            fields=[
                ("partida_id", models.UUIDField(primary_key=True, serialize=False)),
                ("jugador", models.CharField(max_length=150)),
                ("dificultad", models.CharField(
                    choices=[("FACIL", "Fácil"), ("NORMAL", "Normal"), ("DIFICIL", "Difícil")], max_length=10,
                )),
                ("puntaje", models.PositiveIntegerField()),
                ("finalizada_en", models.DateTimeField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name="EnvioRanking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("destino", models.CharField(max_length=255)),
                ("partida", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name="envios_ranking", to="memory.partida",
                )),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("partida", "destino"), name="envio_ranking_unico_por_destino"),
                ],
            },
        ),
    ]
