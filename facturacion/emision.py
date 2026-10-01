"""Lógica de emisión de facturas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


def _validar_venta(venta: Any) -> None:
    if not isinstance(venta, dict):
        raise ValueError("La venta debe ser un diccionario.")

    if not venta.get("id"):
        raise ValueError("La venta debe incluir un identificador.")

    total = venta.get("total")
    if not isinstance(total, (int, float)):
        raise ValueError("La venta debe incluir un total numérico.")

    if total <= 0:
        raise ValueError("El total de la venta debe ser mayor que cero.")

    items = venta.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("La venta debe incluir al menos un ítem.")

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Cada ítem debe ser un diccionario.")
        if not item.get("sku"):
            raise ValueError("Cada ítem debe incluir un SKU.")
        cantidad = item.get("cantidad")
        precio_unitario = item.get("precio_unitario")
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError("La cantidad de cada ítem debe ser un entero mayor que cero.")
        if not isinstance(precio_unitario, (int, float)) or precio_unitario <= 0:
            raise ValueError("El precio unitario de cada ítem debe ser numérico y mayor que cero.")


def _validar_colaboradores(generador_pdf: Any, generador_xml: Any, correo: Any) -> None:
    if generador_pdf is None or not callable(generador_pdf):
        raise ValueError("Se requiere un generador PDF invocable.")
    if generador_xml is None or not callable(generador_xml):
        raise ValueError("Se requiere un generador XML invocable.")
    if correo is None or not hasattr(correo, "enviar") or not callable(correo.enviar):
        raise ValueError("Se requiere un colaborador de correo con método enviar().")


def _procesar_emision_con_colaboradores(
    venta: Dict[str, Any],
    *,
    generador_pdf: Any,
    generador_xml: Any,
    correo: Any,
) -> Dict[str, Any]:
    if not venta.get("pagada"):
        raise ValueError("La venta debe estar pagada para procesarse.")

    cliente = venta.get("cliente") or {}
    destinatario = cliente.get("correo")
    if not destinatario:
        raise ValueError("La venta debe incluir el correo del cliente.")

    pdf = generador_pdf(venta)
    xml = generador_xml(venta)

    asunto = f"Comprobante de factura de la venta {venta.get('id')}"
    cuerpo = "Adjuntamos el PDF visual y el XML de tu factura."
    correo.enviar(destinatario, asunto, cuerpo, [pdf, xml])

    return {
        "exito": True,
        "venta": venta,
        "pdf": pdf,
        "xml": xml,
    }


def emitir(
    venta,
    *,
    generador_pdf: Optional[Any] = None,
    generador_xml: Optional[Any] = None,
    correo: Optional[Any] = None,
) -> Dict[str, Any]:
    """Emite una factura a partir de una venta válida.

    Si se reciben colaboradores inyectables, procesa una venta ya pagada,
    genera el PDF y el XML, y los envía por correo al cliente.
    Si no se reciben colaboradores, conserva el comportamiento histórico de
    devolver un resumen de emisión de factura para la venta validada.
    """

    _validar_venta(venta)

    if generador_pdf is not None or generador_xml is not None or correo is not None:
        _validar_colaboradores(generador_pdf, generador_xml, correo)
        return _procesar_emision_con_colaboradores(
            venta,
            generador_pdf=generador_pdf,
            generador_xml=generador_xml,
            correo=correo,
        )

    factura_id = f"F-{uuid4().hex[:12].upper()}"
    return {
        "estado": "emitida",
        "emitida": True,
        "factura_emitida": True,
        "factura_id": factura_id,
        "venta_id": venta["id"],
        "total": venta["total"] ,
        "moneda": venta.get("moneda", "USD"),
        "emitida_en": datetime.now(timezone.utc).isoformat(),
    }
