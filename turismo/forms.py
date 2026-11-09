import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from .models import Excursion, Perfil

def estilizar(formulario):
    for campo in formulario.fields.values():
        campo.widget.attrs['class'] = ('form-check-input' if isinstance(campo.widget, forms.CheckboxInput)
                                      else 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control')

class ExcursionForm(forms.ModelForm):
    class Meta:
        model = Excursion
        fields = ['region', 'codigo', 'nombre', 'descripcion', 'requisitos', 'tarifa', 'cupos', 'duracion_horas', 'dificultad', 'estado', 'imagen', 'activa']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 4}), 'requisitos': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip().upper()
        # Excluye el registro editado para no considerar su propio código como duplicado.
        repetidos = Excursion.objects.filter(codigo__iexact=codigo).exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError('Ya existe una excursión con este código.')
        return codigo

    def clean_tarifa(self):
        tarifa = self.cleaned_data['tarifa']
        if tarifa < 0:
            raise forms.ValidationError('La tarifa no puede ser negativa.')
        return tarifa

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen and hasattr(imagen, 'content_type'):
            if imagen.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La imagen debe pesar como máximo 5 MB.')
            if imagen.image.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise forms.ValidationError('Usa una imagen JPG, PNG o WEBP.')
        return imagen

class RegistroForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    rut = forms.CharField(label='RUT', help_text='Ejemplo: 12.345.678-5')
    telefono = forms.CharField(label='Teléfono', max_length=20)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'rut', 'telefono', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)

    def clean_rut(self):
        rut = self.cleaned_data['rut'].replace('.', '').replace(' ', '').upper()
        if not re.fullmatch(r'\d{7,8}-[0-9K]', rut):
            raise forms.ValidationError('Escribe un RUT válido con guion y dígito verificador.')
        cuerpo, digito = rut.split('-')
        # Calcula el dígito verificador del RUT mediante módulo 11.
        suma = sum(int(numero) * (2 + indice % 6) for indice, numero in enumerate(reversed(cuerpo)))
        resultado = 11 - suma % 11
        esperado = '0' if resultado == 11 else 'K' if resultado == 10 else str(resultado)
        if digito != esperado:
            raise forms.ValidationError('El dígito verificador del RUT no es correcto.')
        return rut

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if not re.fullmatch(r'\+?[\d\s-]{8,20}', telefono):
            raise forms.ValidationError('Ingresa un teléfono válido.')
        return telefono

    # Guarda usuario y perfil juntos; si falla una operación, revierte ambas.
    @transaction.atomic
    def save(self, commit=True):
        if not commit:
            raise ValueError('El registro debe guardar usuario y perfil juntos.')
        usuario = super().save(commit=True)
        Perfil.objects.create(usuario=usuario, rut=self.cleaned_data['rut'], telefono=self.cleaned_data['telefono'])
        return usuario

class PersonasForm(forms.Form):
    personas = forms.IntegerField(label='Personas', min_value=1, max_value=1000, initial=1,
                                 widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}))
