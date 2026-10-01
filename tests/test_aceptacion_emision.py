import pytest

from facturacion.emision import emitir


class VentaValida:
    pass


def test_C1_emitir_devuelve_factura_emitida_sin_error_para_venta_valida():
    venta = VentaValida()

    factura = emitir(venta)

    assert factura is not None
