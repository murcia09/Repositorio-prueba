"""Operación de emisión de facturas."""

from __future__ import annotations

from typing import Any, Dict


def emitir(venta: dict) -> dict:
    """Emite una factura asociada a una venta válida.

    Parameters
    ----------
    venta:
        Diccionario que debe contener al menos la clave ``venta_id``.

    Returns
    -------
    dict
        Factura emitida con estado ``"emitida"`` y la misma ``venta_id``.

    Raises
    ------
    TypeError
        Si ``venta`` no es un diccionario.
    KeyError
        Si la venta no contiene ``venta_id``.
    ValueError
        Si ``venta_id`` está vacío.
    """

    if not isinstance(venta, dict):
        raise TypeError("venta debe ser un diccionario")

    venta_id = venta["venta_id"]
    if not isinstance(venta_id, str) or not venta_id.strip():
        raise ValueError("venta_id debe ser una cadena no vacía")

    return {"estado": "emitida", "venta_id": venta_id}
