from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from .models import Sucursal, Inventario, Servicio, DetalleAtencion, Venta, Pago
from .forms import InventarioForm, AtencionForm

def InventarioList(request, sucursal_id=None):
    sucursales = Sucursal.objects.all()
    
    if not sucursal_id and sucursales.exists():
        sucursal_actual = sucursales.first()
    elif sucursal_id:
        sucursal_actual = get_object_or_404(Sucursal, id=sucursal_id)
    else:
        sucursal_actual = None

    inventarios = Inventario.objects.filter(sucursal=sucursal_actual) if sucursal_actual else []

    context = {
        'sucursales': sucursales,
        'sucursal_actual': sucursal_actual,
        'inventarios': inventarios,
    }
    return render(request, 'inventariolista.html', context)

def InventarioCreate(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inv = form.save()
            return redirect('inventario_list_sucursal', sucursal_id=inv.sucursal.id)
    else:
        form = InventarioForm()
    return render(request, 'inventarioFrom.html', {'form': form, 'titulo': 'Agregar Stock'})

def InventarioUpdate(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    if request.method == 'POST':
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            inv = form.save()
            return redirect('inventario_list_sucursal', sucursal_id=inv.sucursal.id)
    else:
        form = InventarioForm(instance=inventario)
    return render(request, 'inventarioFrom.html', {'form': form, 'titulo': 'Editar Stock'})

def InventarioDelete(request, pk):
    inventario = get_object_or_404(Inventario, pk=pk)
    sucursal_id = inventario.sucursal.id
    if request.method == 'POST':
        inventario.delete()
        return redirect('inventario_list_sucursal', sucursal_id=sucursal_id)
    return render(request, 'inventarioDelete.html', {'inventario': inventario})

def PlanInventarioView(request):
    sucursales = Sucursal.objects.all()
    context = {
        'sucursales': sucursales,
    }
    return render(request, 'planinventario.html', context)

def PlanInventarioCreate(request):
    sucursales = Sucursal.objects.all()
    if request.method == 'POST':
        return redirect('plan_inventario')
    return render(request, 'planinventarioform.html', {'sucursales': sucursales, 'titulo': 'Crear Nuevo Plan de Inventario'})

# --- Módulo de Servicios y Ventas ---

def ServicioList(request):
    """Muestra el catálogo de servicios estéticos disponibles."""
    servicios = Servicio.objects.all()
    return render(request, 'servicioslista.html', {'servicios': servicios})

def RegistrarAtencion(request):
    """Permite registrar una atención asegurando datos para pruebas."""
    if request.method == 'POST':
        form = AtencionForm(request.POST)
        servicios_ids = request.POST.getlist('servicios')
        metodo_pago = request.POST.get('metodo_pago', 'Efectivo')

        if form.is_valid() and servicios_ids:
            with transaction.atomic():
                atencion = form.save()
                reserva = atencion.reserva
                total_venta = 0
                for s_id in servicios_ids:
                    servicio = Servicio.objects.get(id=s_id)
                    precio = servicio.precio_base
                    DetalleAtencion.objects.create(atencion=atencion, servicio=servicio, precio_aplicado=precio)
                    total_venta += precio

                venta = Venta.objects.create(
                    cliente=getattr(reserva, 'cliente', None),
                    empleado=getattr(reserva, 'trabajador', None),
                    sucursal=getattr(reserva, 'sucursal', None),
                    atencion=atencion,
                    total=total_venta,
                    estado='Pagada',
                )
                Pago.objects.create(venta=venta, monto=total_venta, metodo=metodo_pago)
            return redirect('ventas_list')
    else:
        form = AtencionForm()
        servicios = Servicio.objects.all()
        
        # SI NO HAY SERVICIOS CREADOS, CREAMOS UNOS DE PRUEBA AUTOMÁTICAMENTE
        if not servicios.exists():
            Servicio.objects.create(nombre="Manicure Permanente", precio_base=18500, duracion_minutos=45, descripcion="Esmaltado permanente con diseño base.")
            Servicio.objects.create(nombre="Limpieza Facial Profunda", precio_base=35000, duracion_minutos=60, descripcion="Exfoliación e hidratación profunda.")
            servicios = Servicio.objects.all()

    context = {'form': form, 'servicios': servicios}
    return render(request, 'registroatencion.html', context)
def VentaList(request):
    """Muestra el historial general de ventas realizadas."""
    ventas = Venta.objects.all().order_by('-fecha_hora')
    return render(request, 'ventaslista.html', {'ventas': ventas})

def ActualizarPreciosView(request):
    """Muestra el catálogo de precios actuales y el historial de modificaciones."""
    query = request.GET.get('q', '')
    servicios = Servicio.objects.all()
    if query:
        servicios = servicios.filter(nombre__icontains=query)
    
    context = {
        'servicios': servicios,
        'query': query,
    }
    return render(request, 'actualizarprecio.html', context)

def ModificarPrecioServicioView(request, pk):
    """Permite actualizar el precio base de un servicio específico."""
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        nuevo_precio = request.POST.get('precio_base')
        if nuevo_precio:
            servicio.precio_base = nuevo_precio
            servicio.save()
            return redirect('actualizar_precios')
            
    return render(request, 'modificarprecio.html', {'servicio': servicio})

def CierreCajaView(request):
    """Calcula el resumen diario de ventas y desglose por método de pago para el cierre de caja."""
    ventas_hoy = Venta.objects.all() # Puedes filtrar por fecha actual si lo deseas
    
    total_ventas = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_transacciones = ventas_hoy.count()
    
    # Desglose por método de pago desde el modelo Pago
    pagos = Pago.objects.values('metodo').annotate(subtotal=Sum('monto'))
    desglose = {p['metodo']: p['subtotal'] for p in pagos}

    context = {
        'total_ventas': total_ventas,
        'cantidad_transacciones': cantidad_transacciones,
        'efectivo': desglose.get('Efectivo', 0),
        'tarjeta': desglose.get('Tarjeta', 0),
        'transferencia': desglose.get('Transferencia / Otros', 0),
    }
    return render(request, 'cierre_caja.html', context)
from django.shortcuts import render, redirect, get_object_or_404
from .models import Servicio
