"""Lógica de emisión de facturas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
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


def emitir(venta) -> Dict[str, Any]:
    """Emite una factura a partir de una venta válida.

    Devuelve un diccionario que permite verificar que la factura quedó emitida.
    """

    _validar_venta(venta)

    factura_id = f"F-{uuid4().hex[:12].upper()}"
    return {
        "estado": "emitida",
        "emitida": True,
        "factura_emitida": True,
        "factura_id": factura_id,
        "venta_id": venta["id"],
        "total": venta["total"],
        "moneda": venta.get("moneda", "USD"),
        "emitida_en": datetime.now(timezone.utc).isoformat(),
    }
