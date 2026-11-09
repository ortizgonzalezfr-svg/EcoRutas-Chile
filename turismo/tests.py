from decimal import Decimal
from io import BytesIO
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .forms import ExcursionForm, RegistroForm
from .models import Excursion, Perfil, RegionTuristica

class PruebasEcoRutas(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = RegionTuristica.objects.create(nombre='Los Lagos', descripcion='Bosques y lagos')
        cls.excursion = Excursion.objects.create(region=cls.region, codigo='LAG-001', nombre='Petrohué', descripcion='Senderos de agua turquesa', requisitos='Agua', tarifa=35000, cupos=5, duracion_horas=4)
        cls.personal = User.objects.create_user('operador', password='ClaveSegura123!', is_staff=True)
        cls.viajero = User.objects.create_user('viajero', password='ClaveSegura123!')

    def datos_excursion(self, **cambios):
        datos = {'region': self.region.pk, 'codigo': 'LAG-002', 'nombre': 'Volcán', 'descripcion': 'Paisaje', 'requisitos': 'Agua', 'tarifa': '40000', 'cupos': 10, 'duracion_horas': 5, 'dificultad': 'baja', 'estado': 'disponible', 'activa': 'on'}
        datos.update(cambios)
        return datos

    def test_catalogo_busqueda_filtros_y_detalle(self):
        for texto in ['Petrohué', 'LAG-001', 'turquesa']:
            respuesta = self.client.get(reverse('catalogo'), {'q': texto, 'region': self.region.pk})
            self.assertContains(respuesta, 'Petrohué')
            self.assertEqual(respuesta.context['pagina'].paginator.count, 1)
        self.assertEqual(self.client.get(reverse('detalle', args=['LAG-001'])).status_code, 200)
        self.assertEqual(self.client.get(reverse('catalogo'), {'region': 'x', 'pagina': 'no', 'orden': '-mal'}).status_code, 200)

    def test_paginacion_y_orden(self):
        for indice in range(7):
            Excursion.objects.create(region=self.region, codigo=f'EX-{indice}', nombre=f'Ruta {indice}', descripcion='Ruta', requisitos='Agua', tarifa=indice, cupos=1, duracion_horas=1)
        respuesta = self.client.get(reverse('catalogo'), {'orden': 'precio_mayor', 'pagina': 1})
        self.assertEqual(len(respuesta.context['pagina']), 6)
        self.assertEqual(respuesta.context['pagina'][0], self.excursion)
        self.assertEqual(len(self.client.get(reverse('catalogo'), {'pagina': 2}).context['pagina']), 2)

    def test_acceso_gestion_y_no_mutacion_por_get(self):
        rutas = [reverse('gestion'), reverse('crear_excursion'), reverse('editar_excursion', args=[self.excursion.pk]), reverse('desactivar_excursion', args=[self.excursion.pk])]
        for ruta in rutas:
            self.assertEqual(self.client.get(ruta).status_code, 302)
        self.client.force_login(self.viajero)
        for ruta in rutas:
            self.assertEqual(self.client.post(ruta, self.datos_excursion()).status_code, 302)
        self.client.force_login(self.personal)
        for ruta in rutas:
            self.assertEqual(self.client.get(ruta).status_code, 200)
        self.excursion.refresh_from_db()
        self.assertTrue(self.excursion.activa)

    def test_crud_y_baja_logica(self):
        self.client.force_login(self.personal)
        self.assertEqual(self.client.post(reverse('crear_excursion'), self.datos_excursion()).status_code, 302)
        nueva = Excursion.objects.get(codigo='LAG-002')
        self.client.post(reverse('editar_excursion', args=[nueva.pk]), self.datos_excursion(nombre='Volcán actualizado'))
        nueva.refresh_from_db()
        self.assertEqual(nueva.nombre, 'Volcán actualizado')
        self.client.post(reverse('desactivar_excursion', args=[nueva.pk]))
        nueva.refresh_from_db()
        self.assertFalse(nueva.activa)
        self.assertEqual(self.client.get(reverse('detalle', args=[nueva.codigo])).status_code, 404)

    def test_validacion_codigo_tarifa_y_region_protegida(self):
        self.assertFalse(ExcursionForm(self.datos_excursion(codigo='LAG-001')).is_valid())
        self.assertFalse(ExcursionForm(self.datos_excursion(tarifa='-1')).is_valid())
        with self.assertRaises(ProtectedError):
            self.region.delete()

    def test_itinerario_calculo_limites_y_confirmacion(self):
        agregar = reverse('agregar_itinerario', args=[self.excursion.pk])
        self.assertEqual(self.client.get(agregar).status_code, 405)
        self.client.post(agregar, {'personas': 2})
        self.client.post(agregar, {'personas': 4})
        self.assertEqual(self.client.session['itinerario'][str(self.excursion.pk)], 2)
        respuesta = self.client.get(reverse('itinerario'))
        self.assertEqual(respuesta.context['total'], Decimal('73500'))
        self.assertEqual(respuesta.context['contador_itinerario'], 1)
        self.client.post(reverse('modificar_itinerario', args=[self.excursion.pk]), {'personas': 3})
        self.assertEqual(self.client.session['itinerario'][str(self.excursion.pk)], 3)
        respuesta = self.client.post(reverse('confirmar_itinerario'))
        self.assertContains(respuesta, 'Comprobante simulado')
        self.assertNotIn('itinerario', self.client.session)
        self.excursion.refresh_from_db()
        self.assertEqual(self.excursion.cupos, 5)

    def test_itinerario_eliminar_vaciar_y_cantidades_invalidas(self):
        for valor in [0, -1, '1.5', 'abc', 1001]:
            self.client.post(reverse('agregar_itinerario', args=[self.excursion.pk]), {'personas': valor})
            self.assertNotIn(str(self.excursion.pk), self.client.session.get('itinerario', {}))
        self.client.post(reverse('agregar_itinerario', args=[self.excursion.pk]), {'personas': 1})
        self.client.post(reverse('eliminar_itinerario', args=[self.excursion.pk]))
        self.assertEqual(self.client.session.get('itinerario'), {})
        self.client.post(reverse('vaciar_itinerario'))
        self.assertNotIn('itinerario', self.client.session)

    def test_disponibilidad_revalidada_y_sesiones_aisladas(self):
        self.client.post(reverse('agregar_itinerario', args=[self.excursion.pk]), {'personas': 2})
        otro = Client()
        self.assertNotIn('itinerario', otro.session)
        self.excursion.activa = False
        self.excursion.save()
        self.assertEqual(self.client.post(reverse('confirmar_itinerario')).status_code, 302)
        self.assertIn('itinerario', self.client.session)

    def test_csrf_y_logout_post(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(reverse('agregar_itinerario', args=[self.excursion.pk]), {'personas': 1}).status_code, 403)
        self.client.force_login(self.viajero)
        self.assertEqual(self.client.get(reverse('salir')).status_code, 405)
        self.assertEqual(self.client.post(reverse('salir')).status_code, 302)

    def test_registro_perfil_sin_escalar_privilegios(self):
        datos = {'username': 'nuevo', 'email': 'nuevo@example.com', 'rut': '12.345.678-5', 'telefono': '+56912345678', 'password1': 'AventuraSegura2026!', 'password2': 'AventuraSegura2026!', 'is_staff': 'on', 'rol': 'operador'}
        self.assertEqual(self.client.post(reverse('registro'), datos).status_code, 302)
        usuario = User.objects.get(username='nuevo')
        self.assertFalse(usuario.is_staff)
        self.assertEqual(usuario.perfil.rol, Perfil.Rol.VIAJERO)
        datos.update(username='otro', rut='12.345.678-9')
        self.assertFalse(RegistroForm(datos).is_valid())

    def test_imagen_valida_e_invalida(self):
        import tempfile
        with tempfile.TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta):
            archivo = BytesIO()
            Image.new('RGB', (20, 20), 'green').save(archivo, format='PNG')
            imagen = SimpleUploadedFile('ruta.png', archivo.getvalue(), content_type='image/png')
            self.client.force_login(self.personal)
            self.client.post(reverse('crear_excursion'), {**self.datos_excursion(), 'imagen': imagen})
            self.assertTrue(Excursion.objects.get(codigo='LAG-002').imagen)
            falso = SimpleUploadedFile('falsa.png', b'no-es-imagen', content_type='image/png')
            self.assertFalse(ExcursionForm(self.datos_excursion(), {'imagen': falso}).is_valid())

    def test_poblado_repetible(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta), patch.dict('os.environ', {'DEMO_ADMIN_PASSWORD': 'ClaveDemoAdmin123!', 'DEMO_VIAJERO_PASSWORD': 'ClaveDemoViajero123!'}):
            call_command('poblar_datos', verbosity=0)
            conteos = (Excursion.objects.count(), RegionTuristica.objects.count(), User.objects.count())
            call_command('poblar_datos', verbosity=0)
            self.assertEqual(conteos, (Excursion.objects.count(), RegionTuristica.objects.count(), User.objects.count()))
            self.assertEqual(Excursion.objects.count(), 8)
            self.assertTrue(User.objects.get(username='admin_demo').is_superuser)

    def test_sesion_transitoria_sin_persistencia_en_bd(self):
        from django.contrib.sessions.models import Session
        cantidad_inicial = Session.objects.count()
        self.client.post(reverse('agregar_itinerario', args=[self.excursion.pk]), {'personas': 2})
        self.assertEqual(self.client.session['itinerario'][str(self.excursion.pk)], 2)
        self.assertEqual(Session.objects.count(), cantidad_inicial)

    def test_eliminar_individual_no_disponible_y_corregir_cupos(self):
        self.client.post(reverse('agregar_itinerario', args=[self.excursion.pk]), {'personas': 3})
        self.excursion.cupos = 2
        self.excursion.save()
        respuesta = self.client.get(reverse('itinerario'))
        self.assertContains(respuesta, 'Eliminar excursión')
        self.assertContains(respuesta, reverse('modificar_itinerario', args=[self.excursion.pk]))
        self.assertEqual(respuesta.context['total'], Decimal('0'))
        self.client.post(reverse('modificar_itinerario', args=[self.excursion.pk]), {'personas': 2})
        self.assertFalse(self.client.get(reverse('itinerario')).context['avisos'])
        self.excursion.activa = False
        self.excursion.save()
        self.assertContains(self.client.get(reverse('itinerario')), 'Eliminar excursión')
        self.client.post(reverse('eliminar_itinerario', args=[self.excursion.pk]))
        self.assertEqual(self.client.session['itinerario'], {})

    def test_admin_personalizado_con_filtros_y_edicion(self):
        RegionTuristica.objects.create(nombre='Magallanes', descripcion='Patagonia')
        self.personal.is_superuser = True
        self.personal.save()
        self.client.force_login(self.personal)
        respuesta = self.client.get(reverse('admin:turismo_excursion_changelist'))
        self.assertContains(respuesta, 'EcoRutas Chile - Panel de Control')
        self.assertContains(respuesta, 'form-0-tarifa')
        self.assertContains(respuesta, 'form-0-estado')
        self.assertContains(respuesta, 'region__id__exact')
        self.assertContains(respuesta, 'estado__exact')
        self.assertContains(respuesta, 'activa__exact')
        self.assertContains(self.client.get(reverse('admin:turismo_excursion_change', args=[self.excursion.pk])), 'Identificación')

    def test_ingreso_con_credenciales(self):
        respuesta = self.client.post(reverse('ingresar'), {'username': 'viajero', 'password': 'ClaveSegura123!'})
        self.assertRedirects(respuesta, reverse('catalogo'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.viajero.pk)
