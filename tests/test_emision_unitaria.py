import pytest

from facturacion.emision import emitir


class TimbradorDoble:
    def __init__(self, factura_esperada=None, error=None):
        self.factura_esperada = factura_esperada
        self.error = error
        self.llamadas = []

    def timbrar(self, solicitud):
        self.llamadas.append(solicitud)
        if self.error is not None:
            raise self.error
        return self.factura_esperada


@pytest.mark.parametrize(
    "solicitud,factura_esperada",
    [
        (
            {"folio": "F-1001", "total": 123.45, "cliente": "ACME SA de CV"},
            {"folio": "F-1001", "total": 123.45, "cliente": "ACME SA de CV", "timbrada": True},
        )
    ],
)
def test_emitir_devuelve_exactamente_la_factura_timbrada_y_delega_una_sola_vez(solicitud, factura_esperada):
    timbrador = TimbradorDoble(factura_esperada=factura_esperada)

    resultado = emitir(solicitud, timbrador=timbrador)

    assert resultado is factura_esperada
    assert timbrador.llamadas == [solicitud]


def test_emitir_con_solicitud_vacia_la_pasada_sin_modificar_al_timbrador():
    solicitud = {}
    factura_esperada = {"timbrada": True, "uuid": "UUID-000"}
    timbrador = TimbradorDoble(factura_esperada=factura_esperada)

    resultado = emitir(solicitud, timbrador=timbrador)

    assert resultado is factura_esperada
    assert timbrador.llamadas == [solicitud]


def test_emitir_sin_timbrador_valido_levanta_attribute_error():
    with pytest.raises(AttributeError):
        emitir({"folio": "F-1002"}, timbrador=object())


def test_emitir_propagA_excepcion_del_timbrador():
    solicitud = {"folio": "F-1003"}
    timbrador = TimbradorDoble(error=TimeoutError("timbrado lento"))

    with pytest.raises(TimeoutError, match="timbrado lento"):
        emitir(solicitud, timbrador=timbrador)

    assert timbrador.llamadas == [solicitud]
