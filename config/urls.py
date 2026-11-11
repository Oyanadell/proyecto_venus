"""
Rutas (URLs) principales del proyecto Centro Estético Antonia.
"""
from django.contrib import admin
from django.urls import include, path

from funciones_app.views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    # Grupo 2: Servicios (todas sus rutas están en servicios/urls.py)
    path('servicios/', include('servicios.urls')),

    # Inventario
    path('', InventarioList, name='inventario_list'),
    path('sucursal/<int:sucursal_id>/', InventarioList, name='inventario_list_sucursal'),
    path('plan/', PlanInventarioView, name='plan_inventario'),
    path('plan/nuevo/', PlanInventarioCreate, name='plan_inventario_create'),
    path('nuevo/', InventarioCreate, name='inventario_create'),
    path('editar/<int:pk>/', InventarioUpdate, name='inventario_update'),
    path('eliminar/<int:pk>/', InventarioDelete, name='inventario_delete'),

    # Grupo 2: Ventas
    path('atenciones/registrar/', RegistrarAtencion, name='registrar_atencion'),
    path('ventas/', VentaList, name='ventas_list'),
    path('caja/', CierreCajaView, name='cierre_caja'),
    path('caja/venta/<int:pk>/voucher/', VoucherVentaView, name='voucher_venta'),
]
