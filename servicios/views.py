from django.shortcuts import render, redirect, get_object_or_404

from funciones_app.models import Servicio, Sucursal


def lista_servicios(request):
    # 1. Traer todos los servicios de la base de datos, ordenados por id
    servicios = Servicio.objects.all().order_by('id')

    # 2. Leer lo que la usuaria escribió en el buscador y eligió en la lista
    buscar = request.GET.get('buscar', '')
    categoria = request.GET.get('categoria', '')

    # 3. Si escribió algo, dejar solo los servicios cuyo nombre lo contiene
    if buscar != '':
        servicios = servicios.filter(nombre__icontains=buscar)

    # 4. Si eligió una categoría, dejar solo los de esa categoría
    if categoria != '':
        servicios = servicios.filter(categoria=categoria)

    # 5. Enviar los datos al template
    contexto = {
        'servicios': servicios,
        'buscar': buscar,
        'categoria': categoria,
    }
    return render(request, 'servicios/lista.html', contexto)


def agregar_servicio(request):
    # Si llegó un formulario: crear el servicio y volver a la lista
    if request.method == 'POST':
        servicio = Servicio.objects.create(
            nombre=request.POST['nombre'],
            categoria=request.POST['categoria'],
            duracion_minutos=request.POST['duracion'],
            precio_base=request.POST['precio'],
        )
        # Las casillas marcadas llegan como una lista de ids de sucursales
        servicio.sucursales.set(request.POST.getlist('sucursales'))
        return redirect('lista_servicios')

    # Si solo entró a mirar: mostrar el formulario vacío
    sucursales = Sucursal.objects.all()
    return render(request, 'servicios/nuevo.html', {'sucursales': sucursales})


def cambiar_estado(request):
    # Recibe el id del servicio y lo activa si estaba inactivo (o al revés)
    if request.method == 'POST':
        servicio = Servicio.objects.get(id=request.POST['id'])
        servicio.activo = not servicio.activo
        servicio.save()
    return redirect('lista_servicios')


def editar_servicio(request, id):
    # Buscar el servicio por el id que viene en la dirección (si no existe, error 404)
    servicio = get_object_or_404(Servicio, id=id)

    # Si llegó el formulario: actualizar los datos y volver a la lista
    if request.method == 'POST':
        servicio.nombre = request.POST['nombre']
        servicio.categoria = request.POST['categoria']
        servicio.duracion_minutos = request.POST['duracion']
        servicio.precio_base = request.POST['precio']
        servicio.save()
        servicio.sucursales.set(request.POST.getlist('sucursales'))
        return redirect('lista_servicios')

    # Si solo entró a mirar: mostrar el mismo formulario, ya con los datos del servicio
    contexto = {
        'servicio': servicio,
        'sucursales': Sucursal.objects.all(),
        'ids_locales': [s.id for s in servicio.sucursales.all()],
    }
    return render(request, 'servicios/nuevo.html', contexto)
