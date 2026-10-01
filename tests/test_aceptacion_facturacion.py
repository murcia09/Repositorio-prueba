import pytest

from facturacion.emision import emitir


def test_C1_emitir_con_venta_valida_devuelve_factura_emitida_y_no_falla():
    venta_valida = {
        "id": "V-1001",
        "total": 125.50,
        "moneda": "USD",
        "items": [
            {"sku": "SKU-001", "cantidad": 1, "precio_unitario": 125.50},
        ],
    }

    resultado = emitir(venta_valida)

    assert isinstance(resultado, dict)
    assert resultado.get("estado") == "emitida"
    assert resultado.get("emitida") is True or resultado.get("factura_emitida") is True
