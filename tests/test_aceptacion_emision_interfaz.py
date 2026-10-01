from dataclasses import is_dataclass
from datetime import datetime, timezone

import pytest

from facturacion.emision import Factura, emitir


class VentaPagada:
    def __init__(self, numero=1001, correo="cliente@ejemplo.com"):
        self.numero = numero
        self.correo = correo


class GeneradorPDFDoble:
    def __init__(self):
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return b"PDF-VISUAL"


class GeneradorXMLDoble:
    def __init__(self):
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return b"<xml>FIRMADO</xml>"


class AlmacenDoble:
    def __init__(self):
        self.guardados = []

    def guardar(self, nombre, contenido):
        self.guardados.append((nombre, contenido))


class CorreoDoble:
    def __init__(self):
        self.envios = []

    def enviar(self, destinatario, asunto, cuerpo, adjuntos):
        self.envios.append(
            {
                "destinatario": destinatario,
                "asunto": asunto,
                "cuerpo": cuerpo,
                "adjuntos": adjuntos,
            }
        )


def test_C1_emitir_invoca_generador_pdf_y_generador_xml_con_la_misma_venta():
    venta = VentaPagada()
    generador_pdf = GeneradorPDFDoble()
    generador_xml = GeneradorXMLDoble()
    almacen = AlmacenDoble()
    correo = CorreoDoble()

    factura = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        almacen=almacen,
        correo=correo,
    )

    assert generador_pdf.llamadas == [venta]
    assert generador_xml.llamadas == [venta]
    assert factura.venta is venta


def test_C2_emitir_guarda_pdf_y_xml_con_nombres_diferenciados():
    venta = VentaPagada(numero=7)
    generador_pdf = GeneradorPDFDoble()
    generador_xml = GeneradorXMLDoble()
    almacen = AlmacenDoble()
    correo = CorreoDoble()

    emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        almacen=almacen,
        correo=correo,
    )

    assert almacen.guardados == [
        ("factura-7.pdf", b"PDF-VISUAL"),
        ("factura-7.xml", b"<xml>FIRMADO</xml>"),
    ]


def test_C3_emitir_envia_un_solo_correo_con_pdf_y_xml_adjuntos():
    venta = VentaPagada(correo="cliente@ejemplo.com")
    generador_pdf = GeneradorPDFDoble()
    generador_xml = GeneradorXMLDoble()
    almacen = AlmacenDoble()
    correo = CorreoDoble()

    emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        almacen=almacen,
        correo=correo,
    )

    assert len(correo.envios) == 1
    envio = correo.envios[0]
    assert envio["destinatario"] == "cliente@ejemplo.com"
    assert envio["adjuntos"] == [
        ("factura-7.pdf", b"PDF-VISUAL"),
        ("factura-7.xml", b"<xml>FIRMADO</xml>"),
    ]


def test_C4_emitir_devuelve_factura_emitida_asociada_a_la_misma_venta():
    venta = VentaPagada()
    generador_pdf = GeneradorPDFDoble()
    generador_xml = GeneradorXMLDoble()
    almacen = AlmacenDoble()
    correo = CorreoDoble()

    factura = emitir(
        venta,
        generador_pdf=generador_pdf,
        generador_xml=generador_xml,
        almacen=almacen,
        correo=correo,
    )

    assert isinstance(factura, Factura)
    assert factura.venta is venta
    assert factura.estado == "emitida"
    assert factura.emitida_en.tzinfo == timezone.utc
    assert is_dataclass(factura)