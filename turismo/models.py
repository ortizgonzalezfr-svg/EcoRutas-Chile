from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

class RegionTuristica(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'región turística'
        verbose_name_plural = 'regiones turísticas'

    def __str__(self):
        return self.nombre

class Excursion(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = 'disponible', 'Disponible'
        SUSPENDIDA = 'suspendida', 'Suspendida'
        AGOTADA = 'agotada', 'Agotada'

    class Dificultad(models.TextChoices):
        BAJA = 'baja', 'Baja'
        MEDIA = 'media', 'Media'
        ALTA = 'alta', 'Alta'

    # Impide eliminar una región mientras tenga excursiones asociadas.
    region = models.ForeignKey(RegionTuristica, on_delete=models.PROTECT, related_name='excursiones')
    codigo = models.CharField('código', max_length=24, unique=True, validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Usa letras mayúsculas, números o guiones.')])
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField('descripción')
    requisitos = models.TextField(help_text='Equipo necesario y recomendaciones.')
    tarifa = models.DecimalField('tarifa por persona (CLP)', max_digits=10, decimal_places=0, validators=[MinValueValidator(0)])
    cupos = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    duracion_horas = models.PositiveIntegerField('duración en horas', validators=[MinValueValidator(1)])
    dificultad = models.CharField(max_length=10, choices=Dificultad.choices, default=Dificultad.BAJA)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE)
    imagen = models.ImageField('imagen', upload_to='excursiones/%Y/%m/', blank=True)
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre', 'pk']
        verbose_name = 'excursión'
        verbose_name_plural = 'excursiones'
        constraints = [
            models.CheckConstraint(condition=models.Q(tarifa__gte=0), name='tarifa_no_negativa'),
            models.CheckConstraint(condition=models.Q(duracion_horas__gte=1), name='duracion_positiva'),
        ]

    def __str__(self):
        return f'{self.codigo} · {self.nombre}'

    @property
    def disponible(self):
        return self.activa and self.estado == self.Estado.DISPONIBLE and self.cupos > 0

    @property
    def credito_fotografia(self):
        if self.imagen and '/fotografias/' in self.imagen.name:
            from .fotografias import creditos_fotografias
            return creditos_fotografias().get(self.codigo)
        return None

class Perfil(models.Model):
    class Rol(models.TextChoices):
        VIAJERO = 'viajero', 'Viajero'
        OPERADOR = 'operador', 'Operador'

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    rut = models.CharField('RUT', max_length=12)
    telefono = models.CharField('teléfono', max_length=20)
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.VIAJERO)

    def __str__(self):
        return f'Perfil de {self.usuario.username}'
