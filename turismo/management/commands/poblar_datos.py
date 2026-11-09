import os
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from turismo.models import Excursion, Perfil, RegionTuristica
from turismo.fotografias import CARPETA_FOTOGRAFIAS

class Command(BaseCommand):
    help = 'Crea cuatro regiones, ocho excursiones y dos usuarios de prueba sin duplicados.'

    def add_arguments(self, parser):
        parser.add_argument('--actualizar-fotos', action='store_true', help='Reemplaza las imágenes de las ocho excursiones de ejemplo por las fotografías incluidas.')

    @transaction.atomic
    def handle(self, *args, **options):
        clave_admin = os.getenv('DEMO_ADMIN_PASSWORD')
        clave_viajero = os.getenv('DEMO_VIAJERO_PASSWORD')
        if not clave_admin or not clave_viajero:
            raise CommandError('Configura DEMO_ADMIN_PASSWORD y DEMO_VIAJERO_PASSWORD en .env.')
        regiones = [
            ('Antofagasta', 'Desierto, salares y cielos despejados.'),
            ('Valparaíso', 'Costa, cerros y patrimonio cultural.'),
            ('Los Lagos', 'Volcanes, lagos y bosques templados.'),
            ('Magallanes', 'Paisajes australes y senderos patagónicos.'),
        ]
        destinos = [RegionTuristica.objects.get_or_create(nombre=nombre, defaults={'descripcion': descripcion})[0] for nombre, descripcion in regiones]
        datos = [
            ('ANT-001', 'Valle de la Luna al atardecer', 0, 35000, 18, 5, 'baja', 'Recorre senderos entre formaciones de sal y contempla los colores del desierto.'),
            ('ANT-002', 'Lagunas altiplánicas', 0, 65000, 12, 9, 'media', 'Descubre lagunas y paisajes de altura en una excursión guiada.'),
            ('VAL-001', 'Cerros y colores de Valparaíso', 1, 22000, 20, 4, 'baja', 'Camina por miradores, escaleras y barrios llenos de arte urbano.'),
            ('VAL-002', 'Senderos de La Campana', 1, 40000, 10, 7, 'alta', 'Explora el bosque y sus miradores a través de una caminata de montaña.'),
            ('LAG-001', 'Saltos del Petrohué', 2, 38000, 16, 5, 'baja', 'Disfruta de aguas turquesas y vistas hacia el volcán Osorno.'),
            ('LAG-002', 'Bosques de Chiloé', 2, 48000, 14, 8, 'media', 'Conoce senderos del bosque chilote y la cultura local.'),
            ('MAG-001', 'Miradores de Torres del Paine', 3, 85000, 10, 10, 'media', 'Recorre miradores panorámicos entre lagos y montañas patagónicas.'),
            ('MAG-002', 'Ruta del estrecho de Magallanes', 3, 55000, 15, 6, 'baja', 'Conoce la historia y los paisajes costeros del extremo sur.'),
        ]
        for codigo, nombre, region, tarifa, cupos, horas, dificultad, descripcion in datos:
            excursion, _ = Excursion.objects.get_or_create(codigo=codigo, defaults={
                'nombre': nombre, 'region': destinos[region], 'tarifa': tarifa, 'cupos': cupos,
                'duracion_horas': horas, 'dificultad': dificultad, 'descripcion': descripcion,
                'requisitos': 'Llevar agua, calzado adecuado, protector solar y ropa según el clima. Consultar condiciones antes de viajar.',
            })
            if not excursion.imagen or options['actualizar_fotos']:
                archivo = CARPETA_FOTOGRAFIAS / f'{codigo.lower()}.jpg'
                if not archivo.is_file():
                    raise CommandError(f'Falta la fotografía incluida: {archivo.name}')
                excursion.imagen.save(f'fotografias/{codigo.lower()}.jpg', ContentFile(archivo.read_bytes()))
        for nombre, clave, personal, rut in [
            ('admin_demo', clave_admin, True, '12345678-5'),
            ('viajero_demo', clave_viajero, False, '11111111-1'),
        ]:
            usuario, creado = User.objects.get_or_create(username=nombre, defaults={'is_staff': personal, 'is_superuser': personal, 'email': f'{nombre}@example.com'})
            if creado:
                usuario.set_password(clave)
                usuario.save()
            Perfil.objects.get_or_create(usuario=usuario, defaults={'rut': rut, 'telefono': '+56912345678', 'rol': Perfil.Rol.OPERADOR if personal else Perfil.Rol.VIAJERO})
        self.stdout.write(self.style.SUCCESS('Datos listos: 4 regiones, 8 excursiones y usuarios admin_demo / viajero_demo. Fotografías reemplazadas solo si se indicó --actualizar-fotos.'))
