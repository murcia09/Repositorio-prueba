from datetime import timedelta
from decimal import Decimal

import pytest

from facturacion.errores import EstadoInvalido, FacturaInvalida, PagoRechazado
from facturacion.modelos import EstadoFactura, LineaFactura, MedioPago
from tests.conftest import CAFE


def _timbrada(app, cantidad=2):
    cliente = app.clientes.obtener("c1")
    factura = app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(CAFE, cantidad)]))
    return app.timbrado.timbrar(factura)


def test_pago_en_efectivo_devuelve_el_cambio(app):
    factura = _timbrada(app)  # total 29750
    _, cambio = app.pagos.registrar_pago(factura.identificador, MedioPago.EFECTIVO, 30000)
    assert cambio == Decimal("250.00")
    assert factura.estado == EstadoFactura.PAGADA


def test_pago_con_tarjeta_necesita_referencia(app):
    factura = _timbrada(app)
    with pytest.raises(PagoRechazado, match="referencia"):
        app.pagos.registrar_pago(factura.identificador, MedioPago.TARJETA, factura.total)


def test_pago_parcial_deja_saldo(app):
    factura = _timbrada(app)
    app.pagos.registrar_pago(factura.identificador, MedioPago.TRANSFERENCIA, 10000, referencia="TRX-1")
    assert factura.estado == EstadoFactura.TIMBRADA
    assert factura.saldo == Decimal("19750.00")


def test_no_se_cobra_una_factura_sin_timbrar(app):
    cliente = app.clientes.obtener("c1")
    factura = app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(CAFE, 1)]))
    with pytest.raises(EstadoInvalido):
        app.pagos.registrar_pago(factura.identificador, MedioPago.EFECTIVO, 20000)


def test_anular_cancela_el_timbre_y_devuelve_existencias(app, impuestos):
    factura = _timbrada(app, cantidad=5)
    app.anulacion.anular(factura.identificador, "Error en el precio")
    assert factura.estado == EstadoFactura.ANULADA
    assert factura.timbre.uuid in impuestos.canceladas
    assert app.inventario.disponibles("CAF-250") == 50


def test_fuera_de_plazo_no_se_anula(app):
    factura = _timbrada(app)
    factura.fecha_emision -= timedelta(days=45)
    with pytest.raises(EstadoInvalido, match="plazo"):
        app.anulacion.anular(factura.identificador, "Devolucion")


def test_la_nota_credito_no_supera_el_total(app):
    factura = _timbrada(app)
    app.notas_credito.emitir(factura, 20000, "Devolucion parcial")
    with pytest.raises(FacturaInvalida):
        app.notas_credito.emitir(factura, 10000, "Otra devolucion")
