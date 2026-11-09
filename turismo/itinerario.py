from decimal import Decimal, ROUND_HALF_UP
from .models import Excursion

CLAVE_ITINERARIO = 'itinerario'

TASA_SERVICIO = Decimal('0.05')

def leer_coleccion(sesion):
    coleccion = sesion.get(CLAVE_ITINERARIO, {})
    return coleccion if isinstance(coleccion, dict) else {}

def preparar_resumen(sesion):

    coleccion = leer_coleccion(sesion)
    identificadores = [int(clave) for clave in coleccion if str(clave).isdigit() and len(str(clave)) < 12]
    # Consulta precios y disponibilidad actuales; la sesión conserva identificadores y cantidades.
    excursiones = {str(excursion.pk): excursion for excursion in Excursion.objects.select_related('region').filter(pk__in=identificadores)}
    lineas, avisos, pendientes = [], [], []
    subtotal = Decimal('0')
    for clave, cantidad in coleccion.items():
        excursion = excursiones.get(str(clave))
        if not excursion or not excursion.disponible:
            avisos.append('Una excursión de tu itinerario ya no está disponible. Elimínala o vacía el itinerario.')
            pendientes.append({'pk': clave, 'nombre': excursion.nombre if excursion else 'Excursión no disponible', 'excursion': excursion})
            continue
        if type(cantidad) is not int or cantidad < 1 or cantidad > min(excursion.cupos, 1000):
            avisos.append(f'Revisa las personas para {excursion.nombre}; actualmente hay {excursion.cupos} cupos.')
            pendientes.append({'pk': clave, 'nombre': excursion.nombre, 'excursion': excursion})
            continue
        importe = excursion.tarifa * cantidad
        subtotal += importe
        lineas.append({'excursion': excursion, 'personas': cantidad, 'importe': importe})
    # Usa Decimal y redondeo al peso chileno para calcular el recargo comercial.
    recargo = (subtotal * TASA_SERVICIO).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return {'lineas': lineas, 'avisos': avisos, 'pendientes': pendientes, 'subtotal': subtotal, 'recargo': recargo, 'total': subtotal + recargo}
