from datetime import datetime, timezone

import pytest

from facturacion import Factura, emitir


class VentaValida:
    def __init__(self, identificador=1):
        self.identificador = identificador


def test_emitir_devuelve_factura_con_estado_y_venta_originales():
    venta = VentaValida(identificador=42)
    antes = datetime.now(timezone.utc)

    factura = emitir(venta)

    despues = datetime.now(timezone.utc)
    assert isinstance(factura, Factura)
    assert factura.venta is venta
    assert factura.estado == "emitida"
    assert factura.emitida_en.tzinfo == timezone.utc
    assert antes <= factura.emitida_en <= despues


def test_emitir_rechaza_venta_nula_con_value_error():
    with pytest.raises(ValueError, match="La venta no puede ser None"):
        emitir(None)


def test_factura_exportada_desde_el_paquete_facturacion():
    venta = VentaValida()

    factura = Factura(venta=venta)

    assert factura.venta is venta
    assert factura.estado == "emitida"