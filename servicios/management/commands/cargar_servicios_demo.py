from django.core.management.base import BaseCommand

from funciones_app.models import Servicio, Sucursal

SUCURSALES = [
    ("Providencia", "Av. Providencia 1234"),
    ("Las Condes", "Av. Apoquindo 4500"),
    ("Stgo Centro", "Huérfanos 1020"),
]

# nombre, categoria, minutos, precio, activo, locales (None = todos)
SERVICIOS = [
    ("Corte de Cabello + Lavado", "Cabello", 45, 25000, True, ["Providencia", "Las Condes"]),
    ("Balayage Premium", "Cabello", 180, 85000, True, ["Providencia"]),
    ("Manicura Permanente", "Manicura", 60, 18500, True, ["Providencia", "Las Condes", "Stgo Centro"]),
    ("Limpieza Facial Profunda", "Estetica Facial", 90, 42000, False, ["Las Condes"]),
    ("Pedicura Spa", "Manicura", 75, 22000, True, ["Providencia", "Las Condes"]),
    ("Maquillaje de Novia", "Maquillaje", 120, 95000, True, None),
    ("Perfilado de Cejas", "Estetica Facial", 30, 12000, True, None),
    ("Alisado Keratina", "Cabello", 150, 65000, True, ["Las Condes", "Stgo Centro"]),
    ("Tinte Raíz", "Cabello", 90, 35000, True, ["Providencia", "Stgo Centro"]),
    ("Esmaltado Tradicional", "Manicura", 30, 9000, True, None),
    ("Hidratación Facial", "Estetica Facial", 60, 28000, True, ["Providencia"]),
    ("Maquillaje Social", "Maquillaje", 60, 35000, False, ["Las Condes"]),
]


class Command(BaseCommand):
    help = "Carga sucursales y servicios de ejemplo (no duplica si ya existen)."

    def handle(self, *args, **options):
        sucursales = {}
        for nombre, direccion in SUCURSALES:
            sucursales[nombre], _ = Sucursal.objects.get_or_create(
                nombre=nombre, defaults={"direccion": direccion}
            )

        creados = 0
        for nombre, categoria, minutos, precio, activo, locales in SERVICIOS:
            servicio, nuevo = Servicio.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "categoria": categoria,
                    "duracion_minutos": minutos,
                    "precio_base": precio,
                    "activo": activo,
                },
            )
            if nuevo:
                creados += 1
                nombres = locales or list(sucursales)
                servicio.sucursales.set([sucursales[n] for n in nombres])

        self.stdout.write(self.style.SUCCESS(f"{creados} servicios creados."))
