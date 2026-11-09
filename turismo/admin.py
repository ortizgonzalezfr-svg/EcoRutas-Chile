from django.contrib import admin
from .models import Excursion, Perfil, RegionTuristica

admin.site.site_header = 'EcoRutas Chile - Panel de Control'
admin.site.site_title = 'EcoRutas Chile Admin'
admin.site.index_title = 'Gestión Operativa de Recursos y Servicios'

@admin.register(RegionTuristica)
class RegionTuristicaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']
    search_fields = ['nombre', 'descripcion']

@admin.register(Excursion)
class ExcursionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'region', 'tarifa', 'cupos', 'estado', 'activa']
    list_filter = ['region', 'estado', 'activa', 'dificultad']
    search_fields = ['codigo', 'nombre', 'descripcion']
    list_editable = ['tarifa', 'estado']
    list_select_related = ['region']
    fieldsets = [
        ('Identificación', {'fields': ['codigo', 'nombre', 'region']}),
        ('Experiencia', {'fields': ['descripcion', 'requisitos', 'imagen', 'dificultad', 'duracion_horas']}),
        ('Operación', {'fields': ['tarifa', 'cupos', 'estado', 'activa']}),
    ]

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rut', 'telefono', 'rol']
    search_fields = ['usuario__username', 'rut']
    list_filter = ['rol']
