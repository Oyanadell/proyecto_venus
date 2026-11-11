from django.contrib import admin

from .models import Servicio, Sucursal

# Registrar los modelos permite agregarlos y editarlos desde /admin/
admin.site.register(Sucursal)
admin.site.register(Servicio)
