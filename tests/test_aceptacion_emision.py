from facturacion.emision import emitir


def test_C1_emite_factura_asociada_a_una_venta_valida():
    venta = {"venta_id": "V-001"}

    factura = emitir(venta)

    assert factura is not None
    assert factura["estado"] == "emitida"
    assert factura["venta_id"] == "V-001"
