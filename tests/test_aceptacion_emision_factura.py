from types import SimpleNamespace

from facturacion.emision import emitir


def test_C1_emite_factura_asociada_a_la_venta_y_marcada_como_emitida():
    venta = SimpleNamespace(identificador="VENTA-001")

    factura = emitir(venta)

    assert factura.identificador_venta == venta.identificador
    assert factura.estado == "emitida"
