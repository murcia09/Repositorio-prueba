"""XML de la factura electronica: el documento que se timbra y se entrega.

Lleva emisor, receptor, conceptos, impuestos por tasa y totales. Si la factura ya
esta timbrada, tambien el timbre. Los importes salen de servicios/calculos.py, los
mismos que se usaron para los totales.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from facturacion.config import Configuracion
from facturacion.modelos import Factura
from facturacion.servicios.calculos import desglose_impuestos, importe_neto, impuesto_linea
from facturacion.utilidades.fechas import formato_iso

ESPACIO = "urn:facturacion:demo:1.0"


def generar_xml(factura: Factura, config: Configuracion) -> str:
    raiz = ET.Element(
        "Factura",
        {
            "xmlns": ESPACIO,
            "Serie": factura.serie,
            "Folio": str(factura.folio or ""),
            "Fecha": formato_iso(factura.fecha_emision) if factura.fecha_emision else "",
        },
    )
    ET.SubElement(raiz, "Emisor", {"Nit": config.nit_emisor, "Nombre": config.razon_social_emisor})
    ET.SubElement(raiz, "Receptor", {"Nit": factura.cliente.nit, "Nombre": factura.cliente.nombre})

    conceptos = ET.SubElement(raiz, "Conceptos")
    for linea in factura.lineas:
        ET.SubElement(
            conceptos,
            "Concepto",
            {
                "Codigo": linea.producto.codigo,
                "Descripcion": linea.producto.descripcion,
                "Cantidad": str(linea.cantidad),
                "ValorUnitario": str(linea.producto.precio_unitario),
                "Descuento": str(linea.descuento),
                "Importe": str(importe_neto(linea)),
                "Impuesto": str(impuesto_linea(linea)),
            },
        )

    impuestos = ET.SubElement(raiz, "Impuestos", {"Total": str(factura.impuestos)})
    for tasa, valor in sorted(desglose_impuestos(factura).items()):
        ET.SubElement(impuestos, "Traslado", {"Tasa": str(tasa), "Importe": str(valor)})

    ET.SubElement(
        raiz,
        "Totales",
        {
            "Subtotal": str(factura.subtotal),
            "Descuentos": str(factura.descuentos),
            "Total": str(factura.total),
        },
    )
    if factura.timbre is not None:
        ET.SubElement(
            raiz,
            "Timbre",
            {
                "UUID": factura.timbre.uuid,
                "Sello": factura.timbre.sello,
                "Fecha": formato_iso(factura.timbre.fecha),
                "Proveedor": factura.timbre.proveedor,
            },
        )
    return ET.tostring(raiz, encoding="unicode")


def nombre_archivo_xml(factura: Factura) -> str:
    return f"{factura.identificador}.xml"
