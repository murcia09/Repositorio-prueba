from facturacion.emision import emitir


class TimbradorDoble:
    def __init__(self):
        self.llamadas = []

    def timbrar(self, factura):
        self.llamadas.append(factura)


def test_C1_al_emitir_una_venta_valida_devuelve_factura_emitida_y_timbrar_se_invoca_una_sola_vez():
    venta = {
        "id": "V-1001",
        "total": 125.50,
        "cliente": "ACME SA",
    }
    timbrador = TimbradorDoble()

    factura = emitir(venta, timbrador=timbrador)

    assert isinstance(factura, dict)
    assert factura["estado"] == "emitida"
    assert timbrador.llamadas == [factura]