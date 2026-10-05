import pytest

from facturacion.emision import emitir


def test_emitir_venta_pagada_solicita_pdf_y_xml_y_los_envia_por_correo():
    venta = {
        "id": "VENTA-100",
        "pagada": True,
        "cliente": {"email": "cliente@example.com"},
    }
    llamadas_pdf = []
    llamadas_xml = []
    llamadas_correo = []

    def generador_pdf(venta_recibida):
        llamadas_pdf.append(venta_recibida)
        return "PDF-VISUAL"

    def generador_xml(venta_recibida):
        llamadas_xml.append(venta_recibida)
        return "XML-FIRMADO"

    def enviador_correo(destinatario, asunto, cuerpo, adjuntos):
        llamadas_correo.append(
            {
                "destinatario": destinatario,
                "asunto": asunto,
                "cuerpo": cuerpo,
                "adjuntos": adjuntos,
            }
        )

    resultado = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        enviador_correo=enviador_correo,
    )

    assert llamadas_pdf == [venta]
    assert llamadas_xml == [venta]
    assert llamadas_correo == [
        {
            "destinatario": "cliente@example.com",
            "asunto": "",
            "cuerpo": "",
            "adjuntos": ["PDF-VISUAL", "XML-FIRMADO"],
        }
    ]
    assert resultado == {"estado": "procesada", "venta": venta}


def test_emitir_venta_no_pagada_devuelve_pendiente_y_no_llama_colaboradores():
    venta = {
        "id": "VENTA-101",
        "pagada": False,
        "cliente": {"email": "cliente@example.com"},
    }

    def generador_pdf(_venta):
        raise AssertionError("no debería generarse PDF para una venta no pagada")

    def generador_xml(_venta):
        raise AssertionError("no debería generarse XML para una venta no pagada")

    def enviador_correo(*_args, **_kwargs):
        raise AssertionError("no debería enviarse correo para una venta no pagada")

    resultado = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        enviador_correo=enviador_correo,
    )

    assert resultado == {"estado": "pendiente", "venta": venta}


def test_emitir_venta_pagada_sin_datos_de_correo_lanza_error():
    venta = {
        "id": "VENTA-102",
        "pagada": True,
        "cliente": {"email": "   "},
    }

    def generador_pdf(_venta):
        return "PDF-VISUAL"

    def generador_xml(_venta):
        return "XML-FIRMADO"

    def enviador_correo(*_args, **_kwargs):
        raise AssertionError("no debería enviarse correo si el email es inválido")

    with pytest.raises(ValueError, match="cliente\.email válido"):
        emitir(
            venta,
            generador_pdf=generador_pdf,
            generador_xml=generador_xml,
            enviador_correo=enviador_correo,
        )


def test_emitir_venta_pagada_sin_colaboradores_requeridos_lanza_typeerror():
    venta = {
        "id": "VENTA-103",
        "pagada": True,
        "cliente": {"email": "cliente@example.com"},
    }

    with pytest.raises(TypeError, match="se requieren generador_pdf, generador_xml y enviador_correo"):
        emitir(venta, generador_pdf=lambda _v: None)


def test_emitir_sin_colaboradores_conserva_comportamiento_historico():
    venta = {
        "id": "VENTA-104",
        "total": 10,
        "cliente": "CLIENTE-XYZ",
    }

    resultado = emitir(venta)

    assert resultado == {"estado": "emitida", "venta": venta}
