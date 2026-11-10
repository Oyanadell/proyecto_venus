from django import forms
from .models import Inventario, Atencion, Servicio, Sucursal, Trabajador

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['sucursal', 'producto', 'cantidad']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

class ServicioForm(forms.ModelForm):
    """Formulario para la gestión de servicios estéticos."""
    class Meta:
        model = Servicio
        fields = ["nombre", "precio_base", "duracion_minutos", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "precio_base": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "duracion_minutos": forms.NumberInput(attrs={"class": "form-control", "min": "5"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

class AtencionForm(forms.ModelForm):
    """Formulario para el registro de la atención operativa."""
    metodo_pago = forms.ChoiceField(
        choices=[
            ("Efectivo", "Efectivo"),
            ("Tarjeta", "Tarjeta"),
            ("Transferencia", "Transferencia / Otros"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Atencion
        fields = ["reserva", "observacion"]
        widgets = {
            "reserva": forms.Select(attrs={"class": "form-control"}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class CajaFiltroForm(forms.Form):
    PERIODOS = [
        ("diario", "Día"),
        ("semanal", "Semana"),
        ("mensual", "Mes (26 al 25)"),
    ]

    periodo = forms.ChoiceField(
        choices=PERIODOS,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    fecha = forms.DateField(
        required=False,
        label="Fecha de referencia",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    trabajador = forms.ModelChoiceField(
        queryset=Trabajador.objects.order_by("nombre", "apellido"),
        required=False,
        empty_label="Todo el personal",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.order_by("nombre"),
        required=False,
        empty_label="Todas las sucursales",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    buscar = forms.CharField(
        required=False,
        label="Buscar ventas o servicios",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Cliente, servicio, trabajador, local o venta",
            }
        ),
    )
