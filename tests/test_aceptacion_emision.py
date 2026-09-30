from facturacion.emision import emitir


def test_C1_emite_factura_y_marcar_como_emitida():
    venta = {
        "id_venta": "V-1001",
        "total": 125.50,
        "moneda": "USD",
        "cliente": {
            "id_cliente": "C-42",
            "nombre": "Ana Pérez",
        },
        "lineas": [
            {
                "sku": "SKU-001",
                "cantidad": 1,
                "precio_unitario": 125.50,
            }
        ],
    }

    factura = emitir(venta)

    assert isinstance(factura, dict)
    assert factura.get("emitida") is True
