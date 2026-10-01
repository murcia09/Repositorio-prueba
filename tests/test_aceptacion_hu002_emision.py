from types import SimpleNamespace

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
        "cliente": {
            "correo": "cliente@example.com",
        },
        "total": 125.5,
        "moneda": "USD",
        "items": [
            {"sku": "SKU-001", "cantidad": 1, "precio_unitario": 125.5},
        ],
    }


def test_C1_al_emitir_venta_pagada_se_invoca_el_generador_pdf_con_la_venta_completa(venta_paga):
    generador_pdf = GeneradorPDFDoble()
    generador_xml = GeneradorXMLDoble()
    correo = CorreoDoble()

    emitir(
        venta_paga,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert generador_pdf.llamadas == [venta_paga]


def test_C2_al_emitir_venta_pagada_se_invoca_el_generador_xml_con_la_venta_completa(venta_paga):
    generador_pdf = GeneradorPDFDoble()
    generador_xml = GeneradorXMLDoble()
    correo = CorreoDoble()

    emitir(
        venta_paga,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert generador_xml.llamadas == [venta_paga]


def test_C3_al_emitir_venta_pagada_se_envia_un_solo_correo_con_pdf_y_xml_adjuntos(venta_paga):
    generador_pdf = GeneradorPDFDoble(retorno=b"PDF-DE-LA-VENTA")
    generador_xml = GeneradorXMLDoble(retorno="<xml-de-la-venta/>")
    correo = CorreoDoble()

    emitir(
        venta_paga,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert len(correo.llamadas) == 1
    llamada = correo.llamadas[0]
    assert llamada["destinatario"] == "cliente@example.com"
    assert llamada["adjuntos"] == [b"PDF-DE-LA-VENTA", "<xml-de-la-venta/>"]


def test_C4_al_emitir_venta_pagada_se_devuelve_un_resultado_de_exito_con_referencia_a_la_venta(venta_paga):
    generador_pdf = GeneradorPDFDoble(retorno=b"PDF")
    generador_xml = GeneradorXMLDoble(retorno="<xml/>")
    correo = CorreoDoble()

    resultado = emitir(
        venta_paga,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert isinstance(resultado, dict)
    assert resultado.get("exito") is True
    assert resultado.get("venta") == venta_paga
    assert resultado.get("pdf") == b"PDF"
    assert resultado.get("xml") == "<xml/>"
