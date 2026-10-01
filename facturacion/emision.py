"""Lógica de emisión de facturas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class Factura:
    """Representación mínima de una factura emitida."""

    venta: Any
    emitida_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    estado: str = "emitida"


def emitir(venta) -> Factura:
    """Emite una factura a partir de una venta válida.

    La validación es intencionalmente ligera para cubrir el contrato mínimo:
    cualquier objeto no nulo se acepta como venta válida y devuelve una
    factura emitida consistente.
    """

    if venta is None:
        raise ValueError("La venta no puede ser None")

    return Factura(venta=venta)
