from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("memory", "0002_modo_practica")]

    operations = [
        migrations.AddConstraint(
            model_name="partida",
            constraint=models.CheckConstraint(
                condition=models.Q(practica=False) | models.Q(puntaje=0),
                name="partida_practica_sin_puntaje",
            ),
        ),
    ]
