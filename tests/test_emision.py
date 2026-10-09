import pytest

from facturacion.errores import EstadoInvalido, FacturaInvalida, StockInsuficiente
from facturacion.modelos import EstadoFactura, LineaFactura
from facturacion.servicios.numeracion import GeneradorFolios
from tests.conftest import CAFE, ENVIO, PAN


def test_emitir_asigna_folio_y_descuenta_existencias(app):
    cliente = app.clientes.obtener("c1")
    factura = app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(CAFE, 3)]))
    assert factura.estado == EstadoFactura.EMITIDA
    assert factura.identificador == "FV-1"
    assert app.inventario.disponibles("CAF-250") == 47
    assert app.auditoria.ultimo("factura_emitida").datos["factura"] == "FV-1"


def test_los_folios_son_consecutivos(app):
    cliente = app.clientes.obtener("c1")
    folios = [
        app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(PAN, 1)])).folio
        for _ in range(3)
    ]
    assert folios == [1, 2, 3]


def test_sin_existencias_no_se_emite_ni_se_gasta_folio(app):
    cliente = app.clientes.obtener("c1")
    with pytest.raises(StockInsuficiente):
        app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(PAN, 31)]))
    factura = app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(PAN, 1)]))
    assert factura.folio == 1, "El intento fallido no consumio el folio 1"


def test_los_servicios_no_controlan_inventario(app):
    cliente = app.clientes.obtener("c1")
    factura = app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(ENVIO, 5)]))
    assert factura.estado == EstadoFactura.EMITIDA


def test_una_cantidad_no_valida_se_rechaza(app):
    with pytest.raises(FacturaInvalida):
        app.emision.crear_borrador(app.clientes.obtener("c1"), [LineaFactura(CAFE, 0)])


def test_no_se_emite_dos_veces(app):
    factura = app.emision.emitir(app.emision.crear_borrador(app.clientes.obtener("c1"), [LineaFactura(CAFE, 1)]))
    with pytest.raises(EstadoInvalido):
        app.emision.emitir(factura)


def test_el_generador_de_folios_empieza_donde_se_le_dice():
    folios = GeneradorFolios("FV", inicial=100)
    assert folios.ultimo_asignado is None
    assert folios.siguiente() == 100 and folios.ultimo_asignado == 100
