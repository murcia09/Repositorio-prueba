"""Operación pública para emitir facturas a partir de una venta.

La implementación es deliberadamente ligera para mantener la emisión dentro

de un flujo síncrono simple y predecible.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict


class VentaInvalida(ValueError):
    """Señala que la venta no cumple el contrato mínimo esperado."""


def _validar_venta(venta: Dict[str, Any]) -> None:
    if not isinstance(venta, dict):
        raise VentaInvalida("La venta debe ser un diccionario.")

    if not venta.get("id_venta"):
        raise VentaInvalida("La venta debe incluir 'id_venta'.")

    if "total" not in venta:
        raise VentaInvalida("La venta debe incluir 'total'.")

    if venta.get("cliente") is not None and not isinstance(venta.get("cliente"), dict):
        raise VentaInvalida("'cliente' debe ser un diccionario cuando esté presente.")

    if venta.get("lineas") is not None and not isinstance(venta.get("lineas"), list):
        raise VentaInvalida("'lineas' debe ser una lista cuando esté presente.")


def emitir(venta: dict) -> dict:
    """Emite una factura observable a partir de una venta válida.

    Args:
        venta: Datos de la venta a facturar.

    Returns:
        Un diccionario con la factura emitida y la marca `emitida=True`.

    Raises:
        VentaInvalida: Si la venta no cumple el contrato mínimo esperado.
    """

    _validar_venta(venta)

    factura = deepcopy(venta)
    factura["emitida"] = True
    factura["estado"] = "emitida"
    factura["fecha_emision"] = datetime.now(timezone.utc).isoformat()

    return factura
