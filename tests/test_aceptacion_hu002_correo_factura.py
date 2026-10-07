from types import SimpleNamespace

from facturacion.emision import emitir


class GeneradorPDFStub:
    def __init__(self):
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return b"PDF-DE-LA-FACTURA"


class GeneradorXMLStub:
    def __init__(self):
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return b"XML-FIRMADO-DE-LA-FACTURA"


class AlmacenStub:
    def __init__(self):
        self.guardados = []

    def guardar(self, nombre, contenido):
        self.guardados.append((nombre, contenido))


class CorreoStub:
    def __init__(self):
        self.llamadas = []

    def enviar(self, destinatario, *, adjuntos):
        self.llamadas.append((destinatario, adjuntos))


def test_C1_al_emitir_una_venta_pagada_genera_pdf_xml_y_los_pide_al_almacen():
    venta = SimpleNamespace(identificador="VENTA-001", correo="cliente@ejemplo.com", pagada=True)
    generador_pdf = GeneradorPDFStub()
    generador_xml = GeneradorXMLStub()
    almacen = AlmacenStub()
    correo = CorreoStub()

    factura = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        almacen=almacen,
        correo=correo,
    )

    assert generador_pdf.llamadas == [venta]
    assert generador_xml.llamadas == [venta]
    assert len(almacen.guardados) == 2
    nombres = [nombre for nombre, _ in almacen.guardados]
    contenidos = [contenido for _, contenido in almacen.guardados]
    assert nombres[0] != nombres[1]
    assert any("pdf" in nombre.lower() for nombre in nombres)
    assert any("xml" in nombre.lower() for nombre in nombres)
    assert b"PDF-DE-LA-FACTURA" in contenidos
    assert b"XML-FIRMADO-DE-LA-FACTURA" in contenidos
    assert factura.identificador_venta == venta.identificador


def test_C2_al_emitir_una_venta_pagada_envia_un_correo_con_pdf_y_xml_al_cliente():
    venta = SimpleNamespace(identificador="VENTA-002", correo="cliente@ejemplo.com", pagada=True)
    generador_pdf = GeneradorPDFStub()
    generador_xml = GeneradorXMLStub()
    almacen = AlmacenStub()
    correo = CorreoStub()

    emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        almacen=almacen,
        correo=correo,
    )

    assert len(correo.llamadas) == 1
    destinatario, adjuntos = correo.llamadas[0]
    assert destinatario == venta.correo
    assert isinstance(adjuntos, (list, tuple))
    assert b"PDF-DE-LA-FACTURA" in adjuntos
    assert b"XML-FIRMADO-DE-LA-FACTURA" in adjuntos
