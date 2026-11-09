import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RegionTuristica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.TextField()),
            ],
            options={
                'verbose_name': 'región turística',
                'verbose_name_plural': 'regiones turísticas',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Perfil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=12, verbose_name='RUT')),
                ('telefono', models.CharField(max_length=20, verbose_name='teléfono')),
                ('rol', models.CharField(choices=[('viajero', 'Viajero'), ('operador', 'Operador')], default='viajero', max_length=10)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Excursion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=24, unique=True, validators=[django.core.validators.RegexValidator('^[A-Z0-9-]+$', 'Usa letras mayúsculas, números o guiones.')], verbose_name='código')),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(verbose_name='descripción')),
                ('requisitos', models.TextField(help_text='Equipo necesario y recomendaciones.')),
                ('tarifa', models.DecimalField(decimal_places=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='tarifa por persona (CLP)')),
                ('cupos', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('duracion_horas', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='duración en horas')),
                ('dificultad', models.CharField(choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')], default='baja', max_length=10)),
                ('estado', models.CharField(choices=[('disponible', 'Disponible'), ('suspendida', 'Suspendida'), ('agotada', 'Agotada')], default='disponible', max_length=12)),
                ('imagen', models.ImageField(blank=True, upload_to='excursiones/%Y/%m/', verbose_name='imagen')),
                ('activa', models.BooleanField(default=True)),
                ('creada', models.DateTimeField(auto_now_add=True)),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='excursiones', to='turismo.regionturistica')),
            ],
            options={
                'verbose_name': 'excursión',
                'verbose_name_plural': 'excursiones',
                'ordering': ['nombre', 'pk'],
                'constraints': [models.CheckConstraint(condition=models.Q(('tarifa__gte', 0)), name='tarifa_no_negativa'), models.CheckConstraint(condition=models.Q(('duracion_horas__gte', 1)), name='duracion_positiva')],
            },
        ),
    ]
