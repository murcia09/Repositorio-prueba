import pytest

from facturacion.errores import ErrorTimbrado, EstadoInvalido
from facturacion.modelos import EstadoFactura, LineaFactura
from tests.conftest import CAFE


def _emitida(app):
    cliente = app.clientes.obtener("c1")
    return app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(CAFE, 1)]))


def test_timbrar_deja_la_factura_con_uuid(app, impuestos):
    factura = app.timbrado.timbrar(_emitida(app))
    assert factura.estado == EstadoFactura.TIMBRADA
    assert factura.timbre.uuid in impuestos.timbradas


def test_un_fallo_temporal_se_reintenta(app, impuestos):
    impuestos._fallos_pendientes = 1
    factura = app.timbrado.timbrar(_emitida(app))
    assert factura.estado == EstadoFactura.TIMBRADA
    assert impuestos.llamadas == 2
    assert app.auditoria.ultimo("timbrado_fallido").datos["intento"] == 1


def test_sin_servicio_de_impuestos_el_timbrado_falla(app, impuestos):
    impuestos.disponible = False
    factura = _emitida(app)
    with pytest.raises(ErrorTimbrado):
        app.timbrado.timbrar(factura)
    assert factura.estado == EstadoFactura.EMITIDA, "Queda emitida, sin validez fiscal"


def test_un_servicio_lento_cuenta_como_fallo(app, impuestos):
    impuestos.latencia_s = 5
    with pytest.raises(ErrorTimbrado, match="tardo mas"):
        app.timbrado.timbrar(_emitida(app))


def test_no_se_timbra_dos_veces(app):
    factura = app.timbrado.timbrar(_emitida(app))
    with pytest.raises(EstadoInvalido):
        app.timbrado.timbrar(factura)
