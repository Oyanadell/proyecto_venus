from django.contrib import admin

from .models import Servicio, Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "telefono")


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "duracion_minutos", "precio_base", "activo")
    list_filter = ("categoria", "activo", "sucursales")
    search_fields = ("nombre",)
    filter_horizontal = ("sucursales",)
