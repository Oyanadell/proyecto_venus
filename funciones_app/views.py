from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db.models import Count, Q, Sum
from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    DetalleAtencion,
    DetalleVenta,
    Inventario,
    Pago,
    Servicio,
    Sucursal,
    Trabajador,
    Venta,
)
from .forms import AtencionForm, CajaFiltroForm, InventarioForm, ServicioForm

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

def GestionarServicios(request, pk=None):
    """Permite crear servicios y modificar sus datos y precios."""
    servicio = get_object_or_404(Servicio, pk=pk) if pk is not None else None

    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'El servicio se guardó correctamente.')
            return redirect('gestionar_servicios')
    else:
        form = ServicioForm(instance=servicio)

    return render(request, 'gestionarservicios.html', {
        'form': form,
        'servicio_editando': servicio,
        'servicios': Servicio.objects.all().order_by('nombre'),
    })

def RegistrarAtencion(request):
    """Registra una atención con uno o más servicios en una sola venta."""
    servicios = Servicio.objects.all().order_by("nombre")
    servicios_ids = []
    if request.method == 'POST':
        form = AtencionForm(request.POST)
        servicios_ids = list(dict.fromkeys(request.POST.getlist('servicios')))
        metodo_pago = request.POST.get('metodo_pago', 'Efectivo')
        ids_validos = all(servicio_id.isdecimal() for servicio_id in servicios_ids)
        servicios_seleccionados = (
            list(servicios.filter(pk__in=servicios_ids)) if ids_validos else []
        )

        formulario_valido = form.is_valid()
        servicios_validos = bool(servicios_ids) and ids_validos and (
            len(servicios_seleccionados) == len(servicios_ids)
        )
        if not servicios_ids:
            messages.error(request, 'Selecciona al menos un servicio para la venta.')
        elif not servicios_validos:
            messages.error(request, 'Uno o más servicios seleccionados ya no están disponibles.')

        if formulario_valido and servicios_validos:
            with transaction.atomic():
                atencion = form.save()
                reserva = atencion.reserva
                total_venta = 0
                for servicio in servicios_seleccionados:
                    precio = servicio.precio_base
                    DetalleAtencion.objects.create(
                        atencion=atencion,
                        servicio=servicio,
                        precio_aplicado=precio,
                    )
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

        # SI NO HAY SERVICIOS CREADOS, CREAMOS UNOS DE PRUEBA AUTOMÁTICAMENTE
        if not servicios.exists():
            Servicio.objects.create(nombre="Manicure Permanente", precio_base=18500, duracion_minutos=45, descripcion="Esmaltado permanente con diseño base.")
            Servicio.objects.create(nombre="Limpieza Facial Profunda", precio_base=35000, duracion_minutos=60, descripcion="Exfoliación e hidratación profunda.")
            servicios = Servicio.objects.all().order_by("nombre")

    context = {
        'form': form,
        'servicios': servicios,
        'servicios_ids_seleccionados': servicios_ids,
    }
    return render(request, 'registroatencion.html', context)
def VentaList(request):
    """Muestra el historial general de ventas realizadas."""
    ventas = Venta.objects.all().order_by('-fecha_hora')
    return render(request, 'ventaslista.html', {'ventas': ventas})

def CierreCajaView(request):
    """Muestra ventas, comisiones y servicios del período seleccionado."""
    hoy = timezone.localdate()
    datos_filtro = None
    if request.GET:
        datos_filtro = request.GET.copy()
        datos_filtro.setdefault("periodo", "mensual")
        datos_filtro.setdefault("fecha", hoy.isoformat())
    form = CajaFiltroForm(datos_filtro, initial={"periodo": "mensual", "fecha": hoy})
    filtros_validos = not request.GET or form.is_valid()

    if request.GET and not filtros_validos:
        messages.error(request, "Revisa los filtros de caja e inténtalo nuevamente.")

    filtros = form.cleaned_data if filtros_validos and request.GET else {}
    periodo = filtros.get("periodo") or "mensual"
    fecha_referencia = filtros.get("fecha") or hoy
    trabajador = filtros.get("trabajador")
    sucursal = filtros.get("sucursal")
    busqueda = (filtros.get("buscar") or "").strip()
    fecha_inicio, fecha_fin = _rango_periodo_caja(periodo, fecha_referencia)

    ventas = Venta.objects.none()
    if filtros_validos:
        ventas = Venta.objects.filter(
            estado="Pagada",
            fecha_hora__gte=timezone.make_aware(
                datetime.combine(fecha_inicio, time.min)
            ),
            fecha_hora__lt=timezone.make_aware(
                datetime.combine(fecha_fin + timedelta(days=1), time.min)
            ),
        )
        if trabajador:
            ventas = ventas.filter(empleado=trabajador)
        if sucursal:
            ventas = ventas.filter(sucursal=sucursal)
        if busqueda:
            criterios = (
                Q(cliente__nombre__icontains=busqueda)
                | Q(cliente__apellido__icontains=busqueda)
                | Q(empleado__nombre__icontains=busqueda)
                | Q(empleado__apellido__icontains=busqueda)
                | Q(sucursal__nombre__icontains=busqueda)
                | Q(atencion__detalles__servicio__nombre__icontains=busqueda)
                | Q(detalles__servicio__nombre__icontains=busqueda)
                | Q(detalles__producto__nombre__icontains=busqueda)
            )
            if busqueda.isdecimal():
                criterios |= Q(pk=int(busqueda))
            ventas = ventas.filter(
                pk__in=ventas.filter(criterios).order_by().values("pk").distinct()
            )

        ventas = ventas.select_related("cliente", "empleado", "sucursal").prefetch_related(
            "pagos",
            "atencion__detalles__servicio",
            "detalles__servicio",
            "detalles__producto",
        ).order_by("-fecha_hora")

    resumen = ventas.aggregate(total=Sum("total"), cantidad=Count("pk"))
    total_ventas = resumen["total"] or Decimal("0")
    resumen_por_trabajadora = {}
    for empleado_id, nombre, apellido, porcentaje, total in ventas.values_list(
        "empleado_id",
        "empleado__nombre",
        "empleado__apellido",
        "empleado__porcentaje_comision",
        "total",
    ):
        clave = empleado_id or None
        if clave not in resumen_por_trabajadora:
            resumen_por_trabajadora[clave] = {
                "nombre": (
                    f"{nombre} {apellido}".strip() if empleado_id else "Sin asignar"
                ),
                "porcentaje": porcentaje or 0,
                "ventas": 0,
                "total": Decimal("0"),
                "comision": Decimal("0"),
            }
        comision_venta = (
            total * Decimal(porcentaje or 0) / Decimal("100")
        ).quantize(Decimal("0.01"))
        resumen_por_trabajadora[clave]["ventas"] += 1
        resumen_por_trabajadora[clave]["total"] += total
        resumen_por_trabajadora[clave]["comision"] += comision_venta
    resumen_personal = sorted(
        resumen_por_trabajadora.values(), key=lambda fila: fila["nombre"].casefold()
    )
    comision_total = sum(
        (fila["comision"] for fila in resumen_personal), Decimal("0")
    )
    pagos = Pago.objects.filter(venta__in=ventas).values("metodo").annotate(
        subtotal=Sum("monto")
    ).order_by("metodo")

    servicios_vendidos = []
    detalles_atencion = DetalleAtencion.objects.filter(
        atencion__venta__in=ventas
    ).select_related(
        "servicio",
        "atencion__venta__empleado",
        "atencion__venta__sucursal",
    )
    for detalle in detalles_atencion:
        venta = detalle.atencion.venta
        servicios_vendidos.append({
            "fecha": venta.fecha_hora,
            "venta": venta,
            "servicio": detalle.servicio,
            "cantidad": 1,
            "subtotal": detalle.precio_aplicado,
            "trabajador": venta.empleado,
            "sucursal": venta.sucursal,
        })

    detalles_venta = DetalleVenta.objects.filter(
        venta__in=ventas,
        servicio__isnull=False,
    ).select_related("servicio", "venta__empleado", "venta__sucursal", "venta")
    for detalle in detalles_venta:
        servicios_vendidos.append({
            "fecha": detalle.venta.fecha_hora,
            "venta": detalle.venta,
            "servicio": detalle.servicio,
            "cantidad": detalle.cantidad,
            "subtotal": detalle.subtotal,
            "trabajador": detalle.venta.empleado,
            "sucursal": detalle.venta.sucursal,
        })
    servicios_vendidos.sort(key=lambda detalle: detalle["fecha"], reverse=True)

    return render(request, "cierreCaja.html", {
        "form": form,
        "periodo": periodo,
        "fecha_referencia": fecha_referencia,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_ventas": total_ventas,
        "comision_total": comision_total,
        "cantidad_transacciones": resumen["cantidad"] or 0,
        "resumen_personal": resumen_personal,
        "ventas": ventas,
        "pagos": pagos,
        "servicios_vendidos": servicios_vendidos,
    })


def _rango_periodo_caja(periodo, fecha):
    if periodo == "diario":
        return fecha, fecha
    if periodo == "semanal":
        inicio = fecha - timedelta(days=fecha.weekday())
        return inicio, inicio + timedelta(days=6)

    if fecha.month == 12:
        primer_dia_mes_siguiente = date(fecha.year + 1, 1, 1)
    else:
        primer_dia_mes_siguiente = date(fecha.year, fecha.month + 1, 1)

    if fecha.day >= 26:
        return date(fecha.year, fecha.month, 26), date(
            primer_dia_mes_siguiente.year,
            primer_dia_mes_siguiente.month,
            25,
        )

    if fecha.month == 1:
        mes_anterior = date(fecha.year - 1, 12, 1)
    else:
        mes_anterior = date(fecha.year, fecha.month - 1, 1)
    return date(mes_anterior.year, mes_anterior.month, 26), date(
        fecha.year, fecha.month, 25
    )


def _calcular_iva_incluido(total):
    monto_neto = (total / Decimal("1.19")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return monto_neto, total - monto_neto


def VoucherVentaView(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related(
            "cliente", "empleado", "sucursal", "atencion"
        ).prefetch_related(
            "pagos", "atencion__detalles__servicio", "detalles__servicio",
            "detalles__producto",
        ),
        pk=pk,
    )
    monto_neto, monto_iva = _calcular_iva_incluido(venta.total)
    return render(request, "voucher.html", {
        "venta": venta,
        "razon_social_comercio": settings.VOUCHER_RAZON_SOCIAL,
        "rut_comercio": settings.VOUCHER_RUT_COMERCIO,
        "monto_neto": monto_neto,
        "monto_iva": monto_iva,
        "codigo_transaccion": f"VENTA-{venta.pk:08d}",
        "detalles_atencion": (
            venta.atencion.detalles.all() if venta.atencion else []
        ),
        "detalles_venta": venta.detalles.all(),
    })
from django.shortcuts import render, redirect, get_object_or_404
from .models import Servicio
