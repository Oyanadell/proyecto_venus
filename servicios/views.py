from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from funciones_app.models import Servicio, Sucursal

SERVICIOS_POR_PAGINA = 8


def lista_servicios(request):
    q = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "")
    local = request.GET.get("local", "")

    servicios = Servicio.objects.prefetch_related("sucursales").order_by("id")
    if q:
        servicios = servicios.filter(Q(nombre__icontains=q) | Q(categoria__icontains=q))
    if categoria:
        servicios = servicios.filter(categoria=categoria)
    if local:
        servicios = servicios.filter(sucursales__id=local).distinct()

    pagina = Paginator(servicios, SERVICIOS_POR_PAGINA).get_page(request.GET.get("page"))

    # Conserva los filtros al cambiar de página
    filtros = request.GET.copy()
    filtros.pop("page", None)

    return render(request, "servicios/lista.html", {
        "pagina": pagina,
        "q": q,
        "categoria": categoria,
        "local": local,
        "categorias": Servicio.CATEGORIAS,
        "sucursales": Sucursal.objects.order_by("nombre"),
        "total_sucursales": Sucursal.objects.count(),
        "filtros": filtros.urlencode(),
    })


@require_POST
def cambiar_estado(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    servicio.activo = not servicio.activo
    servicio.save(update_fields=["activo"])
    return redirect(request.POST.get("next") or "servicios:lista")
