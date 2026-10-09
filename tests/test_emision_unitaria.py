import pytest

from facturacion.emision import emitir


class TimbradorDoble:
    def __init__(self, side_effect=None):
        self.llamadas = []
        self.side_effect = side_effect

    def timbrar(self, factura):
        self.llamadas.append(factura)
        if self.side_effect is not None:
            raise self.side_effect


def test_emitir_devuelve_factura_emitida_y_llama_timbrar_una_sola_vez():
    venta = {
        "id": "V-1001",
        "total": 125.50,
        "cliente": "ACME SA",
        "detalle": [{"sku": "A1", "cantidad": 2}],
    }
    timbrador = TimbradorDoble()

    factura = emitir(venta, timbrador=timbrador)

    assert factura == {
        "estado": "emitida",
        "venta": venta,
    }
    assert timbrador.llamadas == [factura]


def test_emitir_no_comparte_referencia_de_venta_y_devuelve_una_factura_independiente():
    venta = {
        "id": "V-1002",
        "total": 0,
        "cliente": "Cliente final",
        "lineas": [],
    }
    timbrador = TimbradorDoble()

    factura = emitir(venta, timbrador=timbrador)
    venta["cliente"] = "Modificado"
    venta["lineas"].append({"sku": "X", "cantidad": 1})

    assert factura["venta"]["cliente"] == "Cliente final"
    assert factura["venta"]["lineas"] == []
    assert timbrador.llamadas[0] is factura
    assert timbrador.llamadas[0]["venta"] is not venta


def test_emitir_admite_venta_vacia_como_caso_borde_y_sigue_timbrando():
    venta = {}
    timbrador = TimbradorDoble()

    factura = emitir(venta, timbrador=timbrador)

    assert factura["estado"] == "emitida"
    assert factura["venta"] == {}
    assert timbrador.llamadas == [factura]


def test_emitir_propagates_error_del_timbrador_sin_ocultarlo():
    venta = {"id": "V-1003"}
    error = RuntimeError("fallo de timbrado")
    timbrador = TimbradorDoble(side_effect=error)

    with pytest.raises(RuntimeError, match="fallo de timbrado"):
        emitir(venta, timbrador=timbrador)

    assert len(timbrador.llamadas) == 1
    assert timbrador.llamadas[0]["estado"] == "emitida"
