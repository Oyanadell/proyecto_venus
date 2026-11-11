"""
Rutas (URLs) principales del proyecto Centro Estético Antonia.
"""
from django.contrib import admin
from django.urls import path

from funciones_app.views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    # Inventario
    path('', InventarioList, name='inventario_list'),
    path('sucursal/<int:sucursal_id>/', InventarioList, name='inventario_list_sucursal'),
    path('plan/', PlanInventarioView, name='plan_inventario'),
    path('plan/nuevo/', PlanInventarioCreate, name='plan_inventario_create'),
    path('nuevo/', InventarioCreate, name='inventario_create'),
    path('editar/<int:pk>/', InventarioUpdate, name='inventario_update'),
    path('eliminar/<int:pk>/', InventarioDelete, name='inventario_delete'),

    # Grupo 2: Servicios y Ventas
    path('servicios/', ServicioList, name='servicios_list'),
    path('servicios/modificar/', GestionarServicios, name='gestionar_servicios'),
    path('servicios/modificar/<int:pk>/', GestionarServicios, name='editar_servicio'),
    path('atenciones/registrar/', RegistrarAtencion, name='registrar_atencion'),
    path('ventas/', VentaList, name='ventas_list'),
    path('caja/', CierreCajaView, name='cierre_caja'),
    path('caja/venta/<int:pk>/voucher/', VoucherVentaView, name='voucher_venta'),
]
