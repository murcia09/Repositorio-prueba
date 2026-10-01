import pytest

from facturacion.emision import emitir


class GeneradorPDFDoble:
    def __init__(self, retorno=b"PDF"):
        self.retorno = retorno
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return self.retorno


class GeneradorXMLDoble:
    def __init__(self, retorno="<xml/>"):
        self.retorno = retorno
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return self.retorno


class CorreoDoble:
    def __init__(self):
        self.llamadas = []

    def enviar(self, destinatario, asunto, cuerpo, adjuntos):
        self.llamadas.append(
            {
                "destinatario": destinatario,
                "asunto": asunto,
                "cuerpo": cuerpo,
                "adjuntos": adjuntos,
            }
        )


@pytest.fixture

def venta_paga():
    return {
        "id": "V-2026-001",
        "pagada": True,
        "cliente": {"correo": "cliente@example.com"},
        "total": 125.5,
        "moneda": "USD",
        "items": [{"sku": "SKU-001", "cantidad": 1, "precio_unitario": 125.5}],
    }


def test_emitir_con_venta_pagada_invoca_generadores_y_envia_correo_con_adjuntos(venta_paga):
    generador_pdf = GeneradorPDFDoble(retorno=b"PDF-DE-LA-VENTA")
    generador_xml = GeneradorXMLDoble(retorno="<xml-de-la-venta/>")
    correo = CorreoDoble()

    resultado = emitir(
        venta_paga,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert generador_pdf.llamadas == [venta_paga]
    assert generador_xml.llamadas == [venta_paga]
    assert len(correo.llamadas) == 1
    llamada = correo.llamadas[0]
    assert llamada["destinatario"] == "cliente@example.com"
    assert llamada["asunto"] == "Comprobante de factura de la venta V-2026-001"
    assert llamada["cuerpo"] == "Adjuntamos el PDF visual y el XML de tu factura."
    assert llamada["adjuntos"] == [b"PDF-DE-LA-VENTA", "<xml-de-la-venta/>"]
    assert resultado == {
        "exito": True,
        "venta": venta_paga,
        "pdf": b"PDF-DE-LA-VENTA",
        "xml": "<xml-de-la-venta/>",
    }


def test_emitir_rechaza_venta_no_pagada_cuando_se_solicita_procesamiento_con_colaboradores(venta_paga):
    venta_paga = dict(venta_paga)
    venta_paga["pagada"] = False

    with pytest.raises(ValueError, match="debe estar pagada"):
        emitir(
            venta_paga,
            generador_pdf=GeneradorPDFDoble(),
            generador_xml=GeneradorXMLDoble(),
            correo=CorreoDoble(),
        )


def test_emitir_rechaza_venta_sin_correo_de_cliente(venta_paga):
    venta_sin_correo = dict(venta_paga)
    venta_sin_correo["cliente"] = {}

    with pytest.raises(ValueError, match="correo del cliente"):
        emitir(
            venta_sin_correo,
            generador_pdf=GeneradorPDFDoble(),
            generador_xml=GeneradorXMLDoble(),
            correo=CorreoDoble(),
        )


@pytest.mark.parametrize(
    "generador_pdf, generador_xml, correo, mensaje",
    [
        (None, GeneradorXMLDoble(), CorreoDoble(), "generador PDF invocable"),
        (GeneradorPDFDoble(), None, CorreoDoble(), "generador XML invocable"),
        (GeneradorPDFDoble(), GeneradorXMLDoble(), None, "colaborador de correo"),
        (object(), GeneradorXMLDoble(), CorreoDoble(), "generador PDF invocable"),
        (GeneradorPDFDoble(), object(), CorreoDoble(), "generador XML invocable"),
        (GeneradorPDFDoble(), GeneradorXMLDoble(), object(), "colaborador de correo"),
    ],
)
def test_emitir_rechaza_colaboradores_invalidos(generador_pdf, generador_xml, correo, mensaje, venta_paga):
    with pytest.raises(ValueError, match=mensaje):
        emitir(
            venta_paga,
            generador_pdf=generador_pdf,
            generador_xml=generador_xml,
            correo=correo,
        )


def test_emitir_propagada_error_del_generador_pdf_y_no_envia_correo(venta_paga):
    class GeneradorPDFQueFalla:
        def __call__(self, venta):
            raise RuntimeError("fallo pdf")

    correo = CorreoDoble()

    with pytest.raises(RuntimeError, match="fallo pdf"):
        emitir(
            venta_paga,
            generador_pdf=GeneradorPDFQueFalla(),
            generador_xml=GeneradorXMLDoble(),
            correo=correo,
        )

    assert correo.llamadas == []


def test_emitir_propagada_error_del_generador_xml_y_no_envia_correo(venta_paga):
    class GeneradorXMLQueFalla:
        def __call__(self, venta):
            raise RuntimeError("fallo xml")

    correo = CorreoDoble()

    with pytest.raises(RuntimeError, match="fallo xml"):
        emitir(
            venta_paga,
            generador_pdf=GeneradorPDFDoble(),
            generador_xml=GeneradorXMLQueFalla(),
            correo=correo,
        )

    assert correo.llamadas == []
