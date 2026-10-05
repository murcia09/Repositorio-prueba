import pytest

from facturacion import emitir


def test_emitir_devuelve_factura_emitida_con_la_venta_asociada():
    venta = {
        "id": "VENTA-001",
        "total": 125.50,
        "moneda": "USD",
        "cliente": "CLIENTE-123",
    }

    factura = emitir(venta)

    assert factura == {
        "estado": "emitida",
        "venta": venta,
    }


def test_emitir_acepta_una_venta_vacia_como_diccionario_valido():
    factura = emitir({})

    assert factura["estado"] == "emitida"
    assert factura["venta"] == {}


def test_emitir_devuelve_una_copia_independiente_de_la_venta():
    venta = {
        "id": "VENTA-002",
        "lineas": [{"sku": "ABC", "cantidad": 1}],
    }

    factura = emitir(venta)
    venta["lineas"][0]["cantidad"] = 99

    assert factura["venta"]["lineas"][0]["cantidad"] == 1


def test_emitir_rechaza_una_entrada_que_no_es_diccionario():
    with pytest.raises(TypeError, match="venta debe ser un diccionario"):
        emitir([{"id": "VENTA-003"}])
