from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

# Los modelos son compartidos por todos los grupos, por eso viven en funciones_app
from funciones_app.models import Servicio, Sucursal

# Categorías permitidas para un servicio
CATEGORIAS = ['Manicure', 'Pedicure', 'Depilación']

# Cuántos servicios se pueden mostrar por página (la usuaria elige uno)
OPCIONES_POR_PAGINA = [5, 10, 15]


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

    # 5. Paginación: cuántos servicios mostrar por página (5, 10 o 15; por defecto 10)
    por_pagina = request.GET.get('por_pagina', '10')
    if not por_pagina.isdigit() or int(por_pagina) not in OPCIONES_POR_PAGINA:
        por_pagina = '10'
    paginador = Paginator(servicios, int(por_pagina))

    # get_page() devuelve la página pedida; si el número no es válido, devuelve la primera o la última
    pagina = paginador.get_page(request.GET.get('pagina'))

    # 6. Enviar los datos al template
    contexto = {
        'pagina': pagina,
        'servicios': pagina.object_list,   # solo los servicios de esta página
        'total_servicios': paginador.count,
        'buscar': buscar,
        'categoria': categoria,
        'por_pagina': int(por_pagina),
        'opciones_por_pagina': OPCIONES_POR_PAGINA,
    }
    return render(request, 'servicios/lista.html', contexto)


def validar_servicio(post, servicio_actual=None):
    """Revisa los datos del formulario. Devuelve los datos limpios y una lista de errores."""
    errores = []

    # Datos tal como los escribió la usuaria (sin espacios al inicio y al final)
    datos = {
        'nombre': post.get('nombre', '').strip(),
        'descripcion': post.get('descripcion', '').strip(),
        'categoria': post.get('categoria', ''),
        'duracion': post.get('duracion', '').strip(),
        'precio': post.get('precio', '').strip(),
        'sucursales': post.getlist('sucursales'),
    }

    # Nombre: obligatorio, máximo 100 letras y que no exista otro servicio con el mismo nombre
    if datos['nombre'] == '':
        errores.append('El nombre del servicio es obligatorio.')
    elif len(datos['nombre']) > 100:
        errores.append('El nombre no puede tener más de 100 caracteres.')
    else:
        repetidos = Servicio.objects.filter(nombre__iexact=datos['nombre'])
        if servicio_actual:
            repetidos = repetidos.exclude(id=servicio_actual.id)
        if repetidos.exists():
            errores.append('Ya existe un servicio con ese nombre.')

    # Categoría: debe ser una de las permitidas
    if datos['categoria'] not in CATEGORIAS:
        errores.append('Selecciona una categoría válida.')

    # Duración: número entero mayor que 0
    if not datos['duracion'].isdigit() or int(datos['duracion']) <= 0:
        errores.append('La duración debe ser un número entero mayor que 0 (en minutos).')

    # Precio: número entero mayor que 0 (pesos chilenos, sin decimales)
    if not datos['precio'].isdigit() or int(datos['precio']) <= 0:
        errores.append('El precio debe ser un número entero mayor que 0.')
    elif int(datos['precio']) > 99999999:
        errores.append('El precio es demasiado alto.')

    # Locales: al menos uno, y todos deben existir
    if len(datos['sucursales']) == 0:
        errores.append('Selecciona al menos un local donde se ofrece el servicio.')
    elif Sucursal.objects.filter(id__in=datos['sucursales']).count() != len(set(datos['sucursales'])):
        errores.append('Uno de los locales seleccionados no existe.')

    return datos, errores


def agregar_servicio(request):
    # Datos vacíos para mostrar el formulario por primera vez
    datos = {'nombre': '', 'descripcion': '', 'categoria': 'Manicure',
             'duracion': '', 'precio': '', 'sucursales': []}

    # Si llegó un formulario: validar, y si todo está bien, crear el servicio
    if request.method == 'POST':
        datos, errores = validar_servicio(request.POST)
        if errores:
            for error in errores:
                messages.error(request, error)
        else:
            servicio = Servicio.objects.create(
                nombre=datos['nombre'],
                descripcion=datos['descripcion'],
                categoria=datos['categoria'],
                duracion_minutos=int(datos['duracion']),
                precio_base=int(datos['precio']),
            )
            # Las casillas marcadas llegan como una lista de ids de sucursales
            servicio.sucursales.set(datos['sucursales'])
            messages.success(request, f'Servicio "{servicio.nombre}" agregado.')
            return redirect('lista_servicios')

    # Mostrar el formulario (vacío, o con lo que escribió si hubo errores)
    contexto = {
        'datos': datos,
        'sucursales': Sucursal.objects.all(),
        'categorias': CATEGORIAS,
    }
    return render(request, 'servicios/nuevo.html', contexto)


def cambiar_estado(request):
    # Activa el servicio si estaba inactivo, y lo desactiva si estaba activo
    if request.method == 'POST':
        servicio = get_object_or_404(Servicio, id=request.POST.get('id'))
        servicio.activo = not servicio.activo
        servicio.save()

        # Volver a la misma página de la lista (solo si es una dirección de /servicios/)
        volver = request.POST.get('volver', '')
        if volver.startswith('/servicios/'):
            return redirect(volver)
    return redirect('lista_servicios')


def editar_servicio(request, id):
    servicio = get_object_or_404(Servicio, id=id)

    # Datos actuales del servicio para rellenar el formulario
    datos = {
        'nombre': servicio.nombre,
        'descripcion': servicio.descripcion or '',
        'categoria': servicio.categoria,
        'duracion': str(servicio.duracion_minutos),
        'precio': str(int(servicio.precio_base)),
        'sucursales': [str(s.id) for s in servicio.sucursales.all()],
    }

    # Si llegó un formulario: validar, y si todo está bien, guardar los cambios
    if request.method == 'POST':
        datos, errores = validar_servicio(request.POST, servicio_actual=servicio)
        if errores:
            for error in errores:
                messages.error(request, error)
        else:
            servicio.nombre = datos['nombre']
            servicio.descripcion = datos['descripcion']
            servicio.categoria = datos['categoria']
            servicio.duracion_minutos = int(datos['duracion'])
            servicio.precio_base = int(datos['precio'])
            servicio.save()
            servicio.sucursales.set(datos['sucursales'])
            messages.success(request, f'Servicio "{servicio.nombre}" actualizado.')
            return redirect('lista_servicios')

    contexto = {
        'servicio': servicio,
        'datos': datos,
        'sucursales': Sucursal.objects.all(),
        'categorias': CATEGORIAS,
    }
    return render(request, 'servicios/nuevo.html', contexto)
