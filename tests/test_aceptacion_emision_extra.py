import pytest

from facturacion.emision import emitir


class TimbradorDoble:
    def __init__(self, retorno=None, error=None):
        self.retorno = retorno
        self.error = error
        self.llamadas = []

    def timbrar(self, solicitud):
        self.llamadas.append(solicitud)
        if self.error is not None:
            raise self.error
        return self.retorno


def test_C1_emitir_delega_una_sola_vez_y_devuelve_exactamente_lo_que_retorna_el_timbrador():
    solicitud = {
        "folio": "F-2001",
        "cliente": "ACME SA de CV",
        "total": 999.99,
    }
    factura_timbrada = {
        "folio": "F-2001",
        "cliente": "ACME SA de CV",
        "total": 999.99,
        "timbrada": True,
        "uuid": "UUID-2001",
    }
    timbrador = TimbradorDoble(retorno=factura_timbrada)

    resultado = emitir(solicitud, timbrador=timbrador)

    assert resultado is factura_timbrada
    assert timbrador.llamadas == [solicitud]


def test_C2_emitir_propagates_timeout_error_sin_convertirlo():
    solicitud = {"folio": "F-2002"}
    error = TimeoutError("timbrado excedido")
    timbrador = TimbradorDoble(error=error)

    with pytest.raises(TimeoutError, match="timbrado excedido") as excinfo:
        emitir(solicitud, timbrador=timbrador)

    assert excinfo.value is error
    assert timbrador.llamadas == [solicitud]
