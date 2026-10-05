from facturacion.emision import emitir


def test_C1_al_emitir_una_venta_pagada_solicita_pdf_y_xml_para_la_misma_venta():
    venta = {
        "id": "VENTA-001",
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

    try:
        emitir(
            venta,
            generador_pdf=generador_pdf,
            generador_xml=generador_xml,
            enviador_correo=enviador_correo,
        )
    except TypeError:
        pass

    assert llamadas_pdf == [venta]
    assert llamadas_xml == [venta]


def test_C2_al_emitir_una_venta_pagada_envia_al_correo_del_cliente_pdf_y_xml():
    venta = {
        "id": "VENTA-002",
        "pagada": True,
        "cliente": {"email": "cliente@example.com"},
    }

    def generador_pdf(venta_recibida):
        return "PDF-VISUAL"

    def generador_xml(venta_recibida):
        return "XML-FIRMADO"

    llamados = []

    def enviador_correo(destinatario, asunto, cuerpo, adjuntos):
        llamados.append(
            {
                "destinatario": destinatario,
                "asunto": asunto,
                "cuerpo": cuerpo,
                "adjuntos": adjuntos,
            }
        )

    try:
        emitir(
            venta,
            generador_pdf=generador_pdf,
            generador_xml=generador_xml,
            enviador_correo=enviador_correo,
        )
    except TypeError:
        pass

    assert llamados == [
        {
            "destinatario": "cliente@example.com",
            "asunto": "",
            "cuerpo": "",
            "adjuntos": ["PDF-VISUAL", "XML-FIRMADO"],
        }
    ]


def test_C3_al_emitir_una_venta_pagada_devuelve_un_resultado_observable_de_procesamiento():
    venta = {
        "id": "VENTA-003",
        "pagada": True,
        "cliente": {"email": "cliente@example.com"},
    }

    def generador_pdf(venta_recibida):
        return "PDF-VISUAL"

    def generador_xml(venta_recibida):
        return "XML-FIRMADO"

    def enviador_correo(destinatario, asunto, cuerpo, adjuntos):
        return None

    resultado = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        enviador_correo=enviador_correo,
    )

    assert resultado == {
        "estado": "procesada",
        "venta": venta,
    }
