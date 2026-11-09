from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('excursion/<str:codigo>/', views.detalle, name='detalle'),
    path('gestion/', views.gestion, name='gestion'),
    path('gestion/nueva/', views.crear_excursion, name='crear_excursion'),
    path('gestion/<int:pk>/editar/', views.editar_excursion, name='editar_excursion'),
    path('gestion/<int:pk>/desactivar/', views.desactivar_excursion, name='desactivar_excursion'),
    path('registro/', views.registro, name='registro'),
    path('ingresar/', auth_views.LoginView.as_view(template_name='turismo/ingresar.html'), name='ingresar'),
    path('salir/', auth_views.LogoutView.as_view(), name='salir'),
    path('itinerario/', views.itinerario, name='itinerario'),
    path('itinerario/<int:pk>/agregar/', views.agregar_itinerario, name='agregar_itinerario'),
    path('itinerario/<int:pk>/modificar/', views.modificar_itinerario, name='modificar_itinerario'),
    path('itinerario/<int:pk>/eliminar/', views.eliminar_itinerario, name='eliminar_itinerario'),
    path('itinerario/vaciar/', views.vaciar_itinerario, name='vaciar_itinerario'),
    path('itinerario/confirmar/', views.confirmar_itinerario, name='confirmar_itinerario'),
]
