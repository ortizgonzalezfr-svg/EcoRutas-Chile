from .itinerario import leer_coleccion

def contador_itinerario(request):
    return {'contador_itinerario': len(leer_coleccion(request.session))}
