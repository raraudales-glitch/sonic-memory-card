from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='partida',
            name='una_partida_en_curso_por_usuario',
        ),
        migrations.AddField(
            model_name='partida',
            name='practica',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddConstraint(
            model_name='partida',
            constraint=models.UniqueConstraint(condition=models.Q(('estado', 'EN_CURSO')), fields=('usuario', 'practica'), name='una_partida_en_curso_por_usuario_y_modo'),
        ),
    ]
