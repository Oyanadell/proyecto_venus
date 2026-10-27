from django.urls import path

from . import views

app_name = "servicios"

urlpatterns = [
    path("", views.lista_servicios, name="lista"),
    path("<int:pk>/estado/", views.cambiar_estado, name="cambiar_estado"),
]
