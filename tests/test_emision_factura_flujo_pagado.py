from types import SimpleNamespace

import pytest

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
        return b"XML-DE-LA-FACTURA"


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


def test_emitir_venta_pagada_genera_guarda_y_envia_pdf_y_xml():
    venta = SimpleNamespace(identificador="VENTA-101", correo="cliente@ejemplo.com", pagada=True)
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

    assert factura.identificador_venta == "VENTA-101"
    assert generador_pdf.llamadas == [venta]
    assert generador_xml.llamadas == [venta]
    assert len(almacen.guardados) == 2
    assert almacen.guardados[0][0] == "VENTA-101-pdf"
    assert almacen.guardados[0][1] == b"PDF-DE-LA-FACTURA"
    assert almacen.guardados[1][0] == "VENTA-101-xml"
    assert almacen.guardados[1][1] == b"XML-DE-LA-FACTURA"
    assert correo.llamadas == [("cliente@ejemplo.com", [b"PDF-DE-LA-FACTURA", b"XML-DE-LA-FACTURA"])]


def test_emitir_venta_no_pagada_con_colaboradores_rechaza_procesamiento():
    venta = SimpleNamespace(identificador="VENTA-102", correo="cliente@ejemplo.com", pagada=False)

    with pytest.raises(ValueError, match="debe estar pagada"):
        emitir(
            venta,
            generador_pdf=GeneradorPDFStub(),
            generador_xml=GeneradorXMLStub(),
            almacen=AlmacenStub(),
            correo=CorreoStub(),
        )


def test_emitir_venta_pagada_sin_todos_los_colaboradores_rechaza_procesamiento():
    venta = SimpleNamespace(identificador="VENTA-103", correo="cliente@ejemplo.com", pagada=True)

    with pytest.raises(ValueError, match="Se requieren generadores, almacenamiento y correo"):
        emitir(
            venta,
            generador_pdf=GeneradorPDFStub(),
            generador_xml=GeneradorXMLStub(),
            almacen=AlmacenStub(),
        )


def test_emitir_venta_pagada_sin_correo_del_cliente_rechaza_procesamiento():
    venta = SimpleNamespace(identificador="VENTA-104", pagada=True)

    with pytest.raises(ValueError, match="correo de cliente válido"):
        emitir(
            venta,
            generador_pdf=GeneradorPDFStub(),
            generador_xml=GeneradorXMLStub(),
            almacen=AlmacenStub(),
            correo=CorreoStub(),
        )
