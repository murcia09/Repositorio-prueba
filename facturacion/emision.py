"""Lógica de emisión de facturas.

La venta ya debe llegar validada por la capa llamante.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


def emitir(venta, *, timbrador) -> dict:
    """Genera una factura emitida y solicita su timbrado una sola vez.

    Parameters
    ----------
    venta:
        Estructura de venta ya validada por la capa superior.
    timbrador:
        Colaborador que expone el método ``timbrar(factura)``.

    Returns
    -------
    dict
        Factura serializable y estable para transporte por API o presentación.
    """

    factura: Dict[str, Any] = {
        "estado": "emitida",
        "venta": deepcopy(venta),
    }
    timbrador.timbrar(factura)
    return factura
