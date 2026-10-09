from facturacion.emision import emitir


class TimbradorDoble:
    def __init__(self, factura_esperada):
        self.factura_esperada = factura_esperada
        self.llamadas = []

    def timbrar(self, solicitud):
        self.llamadas.append(solicitud)
        return self.factura_esperada


def test_C1_emite_y_devuelve_la_factura_timbrada_del_colaborador_inyectado():
    solicitud = {
        "folio": "F-1001",
        "total": 123.45,
        "cliente": "ACME SA de CV",
    }
    factura_timbrada_esperada = {
        "folio": "F-1001",
        "total": 123.45,
        "cliente": "ACME SA de CV",
        "timbrada": True,
        "uuid": "UUID-123",
    }
    timbrador = TimbradorDoble(factura_timbrada_esperada)

    resultado = emitir(solicitud, timbrador=timbrador)

    assert resultado is factura_timbrada_esperada
    assert timbrador.llamadas == [solicitud]
