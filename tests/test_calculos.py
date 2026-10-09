from decimal import Decimal

import pytest

from facturacion.errores import FacturaInvalida
from facturacion.modelos import Cliente, Factura, LineaFactura
from facturacion.servicios.calculos import (
    aplicar_descuento_porcentual,
    calcular_totales,
    desglose_impuestos,
    importe_neto,
)
from facturacion.utilidades.dinero import formatear, redondear
from tests.conftest import CAFE, ENVIO, PAN

CLIENTE = Cliente("c", "Cliente", "1032456789")


def test_totales_con_iva_general_y_exento():
    f = calcular_totales(Factura("FV", CLIENTE, [LineaFactura(CAFE, 2), LineaFactura(PAN, 1)]))
    assert f.subtotal == Decimal("31800.00")
    assert f.impuestos == Decimal("4750.00"), "Solo el cafe paga IVA: 25000 * 0.19"
    assert f.total == Decimal("36550.00")


def test_el_descuento_reduce_la_base_del_iva():
    linea = aplicar_descuento_porcentual(LineaFactura(CAFE, 2), Decimal("0.10"))
    f = calcular_totales(Factura("FV", CLIENTE, [linea]))
    assert f.descuentos == Decimal("2500.00")
    assert f.impuestos == Decimal("4275.00")
    assert f.total == Decimal("26775.00")


def test_un_descuento_mayor_que_la_linea_se_rechaza():
    with pytest.raises(FacturaInvalida):
        importe_neto(LineaFactura(PAN, 1, descuento=Decimal("7000")))


def test_una_factura_sin_lineas_se_rechaza():
    with pytest.raises(FacturaInvalida):
        calcular_totales(Factura("FV", CLIENTE, []))


def test_desglose_por_tasa():
    f = Factura("FV", CLIENTE, [LineaFactura(CAFE, 1), LineaFactura(ENVIO, 1), LineaFactura(PAN, 1)])
    assert desglose_impuestos(f) == {Decimal("0.19"): Decimal("3325.00"), Decimal("0"): Decimal("0.00")}


def test_redondeo_comercial_y_formato():
    assert redondear(Decimal("0.005")) == Decimal("0.01")
    assert formatear(Decimal("1234.5")) == "$ 1.234,50"
