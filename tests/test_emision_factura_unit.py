import pytest
from types import SimpleNamespace

from facturacion.emision import Factura, Venta, emitir


def test_emitir_devuelve_factura_asociada_y_emitida():
    venta = Venta(identificador="VENTA-001")

    factura = emitir(venta)

    assert isinstance(factura, Factura)
    assert factura.identificador_venta == "VENTA-001"
    assert factura.estado == "emitida"


def test_emitir_rechaza_identificador_vacio():
    venta = Venta(identificador="")

    with pytest.raises(ValueError, match="identificador válido"):
        emitir(venta)


def test_emitir_rechaza_venta_sin_identificador():
    venta = SimpleNamespace()

    with pytest.raises(ValueError, match="identificador válido"):
        emitir(venta)
