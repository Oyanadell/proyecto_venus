from django.urls import path

from . import views

# Estas rutas quedan bajo /servicios/ (ver config/urls.py)
urlpatterns = [
    path('', views.lista_servicios, name='lista_servicios'),
    path('nuevo/', views.agregar_servicio, name='agregar_servicio'),
    path('estado/', views.cambiar_estado, name='cambiar_estado'),
    path('<int:id>/editar/', views.editar_servicio, name='editar_servicio'),
]
