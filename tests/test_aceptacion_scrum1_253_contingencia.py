from facturacion.emision import emitir, sincronizar_facturas_pendientes


def test_C1_y_C4_sincroniza_cada_factura_pendiente_en_orden_y_devuelve_resumen_observable():
    facturas_pendientes = [
        {"id": "FAC-001", "cliente": "CLIENTE-1"},
        {"id": "FAC-002", "cliente": "CLIENTE-2"},
    ]
    llamadas = []

    def sincronizador(factura):
        llamadas.append(factura)
        return f"remota-{factura['id']}"

    resultado = sincronizar_facturas_pendientes(
        facturas_pendientes,
        sincronizador=sincronizador,
    )

    assert llamadas == facturas_pendientes
    assert resultado == {
        "total_procesadas": 2,
        "procesadas_correctamente": [
            {"id": "FAC-001", "cliente": "CLIENTE-1", "id_remoto": "remota-FAC-001"},
            {"id": "FAC-002", "cliente": "CLIENTE-2", "id_remoto": "remota-FAC-002"},
        ],
        "fallidas": [],
    }


def test_C2_cuando_no_hay_facturas_pendientes_no_invoca_al_sincronizador_y_devuelve_no_op():
    llamadas = []

    def sincronizador(factura):
        llamadas.append(factura)
        raise AssertionError("no debería llamarse cuando la cola está vacía")

    resultado = sincronizar_facturas_pendientes([], sincronizador=sincronizador)

    assert llamadas == []
    assert resultado == {
        "total_procesadas": 0,
        "procesadas_correctamente": [],
        "fallidas": [],
    }


def test_C3_emitir_en_modo_contingencia_conserva_la_venta_y_devuelve_un_estado_observable():
    venta = {
        "id": "VENTA-900",
        "pagada": True,
        "cliente": {"email": "cliente@example.com"},
    }

    def generador_pdf(venta_recibida):
        assert venta_recibida == venta
        return "PDF-VISUAL"

    def generador_xml(venta_recibida):
        assert venta_recibida == venta
        return "XML-FIRMADO"

    llamados_correo = []

    def enviador_correo(destinatario, asunto, cuerpo, adjuntos):
        llamados_correo.append(
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

    assert resultado == {
        "estado": "procesada",
        "venta": venta,
    }
    assert llamados_correo == [
        {
            "destinatario": "cliente@example.com",
            "asunto": "",
            "cuerpo": "",
            "adjuntos": ["PDF-VISUAL", "XML-FIRMADO"],
        }
    ]
