import pytest

from facturacion.emision import emitir


def test_emitir_devuelve_factura_emitida_asociada_a_venta_valida():
    venta = {"venta_id": "V-001"}

    factura = emitir(venta)

    assert factura == {"estado": "emitida", "venta_id": "V-001"}


@pytest.mark.parametrize(
    "venta_id",
    ["V-002", "  V-003  "],
)
def test_emitir_con_venta_id_no_vacio_devuelve_estado_emitida(venta_id):
    factura = emitir({"venta_id": venta_id})

    assert factura["estado"] == "emitida"
    assert factura["venta_id"] == venta_id
