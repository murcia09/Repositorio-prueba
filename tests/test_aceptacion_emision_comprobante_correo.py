from facturacion.emision import emitir


class GeneradorPdfDoble:
    def __init__(self, retorno):
        self.retorno = retorno
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return self.retorno


class GeneradorXmlDoble:
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
        self.llamadas.append(
            {
                "destinatario": destinatario,
                "pdf": pdf,
                "xml": xml,
            }
        )


def test_C1_solicita_pdf_xml_y_envia_al_correo_del_cliente():
    venta = {
        "venta_id": "V-1001",
        "correo_cliente": "cliente@example.com",
        "pagada": True,
    }
    generador_pdf = GeneradorPdfDoble("PDF-VISUAL")
    generador_xml = GeneradorXmlDoble("XML-FIRMADO")
    correo = CorreoDoble()

    emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert generador_pdf.llamadas == [venta]
    assert generador_xml.llamadas == [venta]
    assert correo.llamadas == [
        {
            "destinatario": "cliente@example.com",
            "pdf": "PDF-VISUAL",
            "xml": "XML-FIRMADO",
        }
    ]


def test_C2_devuelve_factura_con_venta_id_y_estado_emitida():
    venta = {
        "venta_id": "V-2002",
        "correo_cliente": "comprador@example.com",
        "pagada": True,
    }
    generador_pdf = GeneradorPdfDoble("PDF")
    generador_xml = GeneradorXmlDoble("XML")
    correo = CorreoDoble()

    factura = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        correo=correo,
    )

    assert factura["venta_id"] == "V-2002"
    assert factura["estado"] == "emitida"
