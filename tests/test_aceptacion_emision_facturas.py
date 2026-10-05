from facturacion.emision import emitir


def test_C1_al_emitir_una_venta_valida_devuelve_factura_emitida_asociada_a_la_venta():
    venta = {
        "id": "VENTA-001",
        "total": 125.50,
        "moneda": "USD",
        "cliente": "CLIENTE-123",
    }

    factura = emitir(venta)

    assert isinstance(factura, dict)
    assert factura["estado"] == "emitida"
    assert factura["venta"] == venta
