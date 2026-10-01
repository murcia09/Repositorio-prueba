import pytest

from facturacion.emision import emitir


class GeneradorDoble:
    def __init__(self, retorno):
        self.retorno = retorno
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return self.retorno


class CorreoDoble:
    def __init__(self):
        self.llamadas = []

    def enviar(self, destinatario, *, pdf, xml):
        self.llamadas.append({"destinatario": destinatario, "pdf": pdf, "xml": xml})


def test_emitir_venta_pagada_envia_pdf_y_xml_al_correo_del_cliente():
    venta = {
        "venta_id": "V-9001",
        "correo_cliente": "cliente@example.com",
        "pagada": True,
    }
    generador_pdf = GeneradorDoble("PDF-VISUAL")
    generador_xml = GeneradorDoble("XML-FIRMADO")
    correo = CorreoDoble()

    factura = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert factura == {"estado": "emitida", "venta_id": "V-9001"}
    assert generador_pdf.llamadas == [venta]
    assert generador_xml.llamadas == [venta]
    assert correo.llamadas == [
        {"destinatario": "cliente@example.com", "pdf": "PDF-VISUAL", "xml": "XML-FIRMADO"}
    ]


@pytest.mark.parametrize(
    "venta",
    [
        {"venta_id": "V-9002", "correo_cliente": "cliente@example.com", "pagada": False},
        {"venta_id": "V-9003", "correo_cliente": "cliente@example.com"},
        {"venta_id": "V-9004", "correo_cliente": "cliente@example.com", "pagada": None},
    ],
)
def test_emitir_venta_no_pagada_rechaza_envio_de_comprobante(venta):
    generador_pdf = GeneradorDoble("PDF")
    generador_xml = GeneradorDoble("XML")
    correo = CorreoDoble()

    with pytest.raises(ValueError, match="la venta debe estar pagada para enviar comprobante"):
        emitir(
            venta,
            generador_pdf=generador_pdf,
            generador_xml=generador_xml,
            correo=correo,
        )

    assert generador_pdf.llamadas == []
    assert generador_xml.llamadas == []
    assert correo.llamadas == []


def test_emitir_venta_pagada_sin_correo_cliente_lanza_valueerror():
    venta = {"venta_id": "V-9005", "pagada": True, "correo_cliente": "   "}
    generador_pdf = GeneradorDoble("PDF")
    generador_xml = GeneradorDoble("XML")
    correo = CorreoDoble()

    with pytest.raises(ValueError, match="correo_cliente debe ser una cadena no vacía"):
        emitir(
            venta,
            generador_pdf=generador_pdf,
            generador_xml=generador_xml,
            correo=correo,
        )

    assert generador_pdf.llamadas == []
    assert generador_xml.llamadas == []
    assert correo.llamadas == []


def test_emitir_venta_pagada_sin_dependencias_completas_lanza_valueerror():
    venta = {"venta_id": "V-9006", "correo_cliente": "cliente@example.com", "pagada": True}

    with pytest.raises(ValueError, match="se requieren generador_pdf, generador_xml y correo"):
        emitir(venta, generador_pdf=GeneradorDoble("PDF"))
