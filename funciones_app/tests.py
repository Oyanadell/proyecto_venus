from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from .models import (
    Atencion,
    Cliente,
    DetalleAtencion,
    Pago,
    Reserva,
    Servicio,
    Sucursal,
    Trabajador,
    Venta,
)
from .views import _calcular_iva_incluido, _rango_periodo_caja


class RangoPeriodoCajaTests(SimpleTestCase):
    def test_rango_diario(self):
        fecha = date(2026, 11, 10)

        self.assertEqual(_rango_periodo_caja("diario", fecha), (fecha, fecha))

    def test_rango_semanal_comienza_el_lunes(self):
        self.assertEqual(
            _rango_periodo_caja("semanal", date(2026, 11, 11)),
            (date(2026, 11, 9), date(2026, 11, 15)),
        )

    def test_periodo_mensual_abarca_del_26_al_25(self):
        self.assertEqual(
            _rango_periodo_caja("mensual", date(2026, 11, 10)),
            (date(2026, 10, 26), date(2026, 11, 25)),
        )
        self.assertEqual(
            _rango_periodo_caja("mensual", date(2026, 11, 28)),
            (date(2026, 11, 26), date(2026, 12, 25)),
        )

    def test_periodo_mensual_cruza_el_cambio_de_ano(self):
        self.assertEqual(
            _rango_periodo_caja("mensual", date(2027, 1, 10)),
            (date(2026, 12, 26), date(2027, 1, 25)),
        )


class DesgloseIvaVoucherTests(SimpleTestCase):
    def test_el_iva_incluido_suma_al_total(self):
        total = Decimal("11900")
        neto, iva = _calcular_iva_incluido(total)

        self.assertEqual(neto, Decimal("10000"))
        self.assertEqual(iva, Decimal("1900"))
        self.assertEqual(neto + iva, total)

    def test_iva_incluido_redondea_el_neto_a_pesos(self):
        neto, iva = _calcular_iva_incluido(Decimal("1000"))

        self.assertEqual(neto, Decimal("840"))
        self.assertEqual(iva, Decimal("160"))


class RegistrarAtencionMultiplesServiciosTests(TestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(
            nombre="Local de prueba",
            direccion="Direccion de prueba",
        )
        self.cliente = Cliente.objects.create(
            rut="TEST-CLIENTE",
            nombre="Cliente",
            apellido="Prueba",
        )
        self.trabajador = Trabajador.objects.create(
            sucursal=self.sucursal,
            rut="TEST-TRABAJADOR",
            nombre="Trabajadora",
            apellido="Prueba",
        )
        self.reserva = Reserva.objects.create(
            cliente=self.cliente,
            trabajador=self.trabajador,
            sucursal=self.sucursal,
            fecha=date(2026, 11, 10),
            hora_inicio="10:00",
            hora_fin="11:00",
        )
        self.servicio_uno = Servicio.objects.create(
            nombre="Servicio uno",
            precio_base=Decimal("10000"),
            duracion_minutos=30,
        )
        self.servicio_dos = Servicio.objects.create(
            nombre="Servicio dos",
            precio_base=Decimal("15000"),
            duracion_minutos=45,
        )

    def test_registra_varios_servicios_en_una_venta(self):
        response = self.client.post(
            "/atenciones/registrar/",
            {
                "reserva": self.reserva.pk,
                "metodo_pago": "Efectivo",
                "servicios": [self.servicio_uno.pk, self.servicio_dos.pk],
            },
        )

        self.assertRedirects(response, "/ventas/")
        venta = Venta.objects.get()
        self.assertEqual(venta.total, Decimal("25000"))
        self.assertEqual(venta.atencion.detalles.count(), 2)
        self.assertEqual(Pago.objects.get(venta=venta).monto, Decimal("25000"))

    def test_requiere_seleccionar_al_menos_un_servicio(self):
        response = self.client.post(
            "/atenciones/registrar/",
            {
                "reserva": self.reserva.pk,
                "metodo_pago": "Efectivo",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selecciona al menos un servicio")
        self.assertEqual(Atencion.objects.count(), 0)
        self.assertEqual(Venta.objects.count(), 0)

    def test_rechaza_ids_de_servicio_invalidos_sin_crear_venta(self):
        response = self.client.post(
            "/atenciones/registrar/",
            {
                "reserva": self.reserva.pk,
                "metodo_pago": "Efectivo",
                "servicios": ["no-es-un-id"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Uno o más servicios seleccionados")
        self.assertEqual(Atencion.objects.count(), 0)
        self.assertEqual(Venta.objects.count(), 0)
