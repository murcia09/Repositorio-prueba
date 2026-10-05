"""Lógica de emisión de facturas."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


def emitir(venta: Dict[str, Any]) -> Dict[str, Any]:
    """Emite una factura asociada a una venta válida.

    La función devuelve un diccionario con el estado 'emitida' y la venta
    original asociada a la factura.
    """
    if not isinstance(venta, dict):
        raise TypeError("venta debe ser un diccionario")

    return {
        "estado": "emitida",
        "venta": deepcopy(venta),
    }
