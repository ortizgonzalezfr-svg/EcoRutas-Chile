from uuid import uuid4
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import ExcursionForm, PersonasForm, RegistroForm
from .itinerario import CLAVE_ITINERARIO, leer_coleccion, preparar_resumen
from .models import Excursion, RegionTuristica

def catalogo(request):

    destinos_portada = Excursion.objects.filter(
        activa=True, estado=Excursion.Estado.DISPONIBLE,
        codigo__in=['ANT-002', 'LAG-001', 'MAG-001'],
    ).exclude(imagen='').select_related('region').order_by('codigo')
    # Obtiene también la región para evitar consultas adicionales por cada resultado.
    excursiones = Excursion.objects.filter(activa=True).select_related('region')
    busqueda = request.GET.get('q', '').strip()
    region = request.GET.get('region', '')
    orden = request.GET.get('orden', 'nombre')
    if busqueda:
        excursiones = excursiones.filter(Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda) | Q(descripcion__icontains=busqueda))
    if region.isdigit() and len(region) < 12:
        excursiones = excursiones.filter(region_id=int(region))
    # Limita el ordenamiento a los campos permitidos por la aplicación.
    ordenes = {'nombre': 'nombre', 'precio_menor': 'tarifa', 'precio_mayor': '-tarifa', 'duracion': 'duracion_horas'}
    excursiones = excursiones.order_by(ordenes.get(orden, 'nombre'), 'pk')
    parametros = request.GET.copy()
    parametros.pop('pagina', None)
    return render(request, 'turismo/catalogo.html', {
        'pagina': Paginator(excursiones, 6).get_page(request.GET.get('pagina')),
        'regiones': RegionTuristica.objects.all(), 'busqueda': busqueda, 'region_seleccionada': region,
        'orden': orden, 'parametros': parametros.urlencode(),
        'destinos_portada': destinos_portada,
    })

def detalle(request, codigo):
    excursion = get_object_or_404(Excursion.objects.select_related('region'), codigo=codigo, activa=True)
    return render(request, 'turismo/detalle.html', {'excursion': excursion, 'formulario': PersonasForm()})

# La gestión requiere una sesión iniciada y permisos de personal.
@login_required
@user_passes_test(lambda usuario: usuario.is_staff)
def gestion(request):
    return render(request, 'turismo/gestion.html', {'excursiones': Excursion.objects.select_related('region').all()})

def guardar_excursion(request, excursion=None):
    formulario = ExcursionForm(request.POST or None, request.FILES or None, instance=excursion)
    if request.method == 'POST' and formulario.is_valid():
        formulario.save()
        messages.success(request, 'Excursión guardada correctamente.')
        return redirect('gestion')
    return render(request, 'turismo/formulario.html', {'formulario': formulario, 'titulo': 'Editar excursión' if excursion else 'Nueva excursión'})

# La gestión requiere una sesión iniciada y permisos de personal.
@login_required
@user_passes_test(lambda usuario: usuario.is_staff)
def crear_excursion(request):
    return guardar_excursion(request)

# La gestión requiere una sesión iniciada y permisos de personal.
@login_required
@user_passes_test(lambda usuario: usuario.is_staff)
def editar_excursion(request, pk):
    return guardar_excursion(request, get_object_or_404(Excursion, pk=pk))

# La gestión requiere una sesión iniciada y permisos de personal.
@login_required
@user_passes_test(lambda usuario: usuario.is_staff)
def desactivar_excursion(request, pk):
    excursion = get_object_or_404(Excursion, pk=pk)
    if request.method == 'POST':
        # Retira la excursión del catálogo sin eliminar su registro.
        excursion.activa = False
        excursion.save(update_fields=['activa'])
        messages.success(request, 'Excursión desactivada. Puedes reactivarla desde Editar.')
        return redirect('gestion')
    return render(request, 'turismo/desactivar.html', {'excursion': excursion})

def registro(request):
    formulario = RegistroForm(request.POST or None)
    if request.method == 'POST' and formulario.is_valid():
        usuario = formulario.save()
        login(request, usuario)
        messages.success(request, 'Tu cuenta de viajero está lista.')
        return redirect('catalogo')
    return render(request, 'turismo/registro.html', {'formulario': formulario})

def itinerario(request):
    return render(request, 'turismo/itinerario.html', preparar_resumen(request.session))

def establecer_personas(request, pk, acumular):
    excursion = get_object_or_404(Excursion, pk=pk)
    formulario = PersonasForm(request.POST)
    if not formulario.is_valid():
        messages.error(request, 'Ingresa una cantidad entera entre 1 y 1000 personas.')
        return redirect('itinerario')
    coleccion = leer_coleccion(request.session).copy()
    anteriores = coleccion.get(str(pk), 0)
    if type(anteriores) is not int:
        anteriores = 0
    # Al agregar acumula personas; al modificar reemplaza la cantidad anterior.
    cantidad = formulario.cleaned_data['personas'] + (anteriores if acumular else 0)
    if not excursion.disponible or cantidad > min(excursion.cupos, 1000):
        messages.error(request, 'La excursión no está disponible o la cantidad supera los cupos actuales.')
        return redirect('itinerario')
    if not acumular and str(pk) not in coleccion:
        messages.error(request, 'Primero agrega la excursión al itinerario.')
        return redirect('itinerario')
    coleccion[str(pk)] = cantidad
    # Reasigna la colección para que Django detecte el cambio en la sesión.
    request.session[CLAVE_ITINERARIO] = coleccion
    messages.success(request, 'Itinerario actualizado.')
    return redirect('itinerario')

@require_POST
def agregar_itinerario(request, pk):
    return establecer_personas(request, pk, True)

@require_POST
def modificar_itinerario(request, pk):
    return establecer_personas(request, pk, False)

@require_POST
def eliminar_itinerario(request, pk):
    coleccion = leer_coleccion(request.session).copy()
    coleccion.pop(str(pk), None)
    # Reasigna la colección para que Django detecte el cambio en la sesión.
    request.session[CLAVE_ITINERARIO] = coleccion
    return redirect('itinerario')

@require_POST
def vaciar_itinerario(request):
    request.session.pop(CLAVE_ITINERARIO, None)
    messages.info(request, 'El itinerario quedó vacío.')
    return redirect('itinerario')

@require_POST
def confirmar_itinerario(request):
    # Revalida precios, cupos y disponibilidad antes de emitir el comprobante.
    resumen = preparar_resumen(request.session)
    if resumen['avisos'] or not resumen['lineas']:
        messages.error(request, 'Revisa el itinerario antes de generar la solicitud.')
        return redirect('itinerario')
    resumen.update({'folio': uuid4().hex[:12].upper(), 'fecha': timezone.now()})
    # La solicitud es simulada: vacía la selección sin reservar ni descontar cupos.
    request.session.pop(CLAVE_ITINERARIO, None)

    return render(request, 'turismo/comprobante.html', resumen)
