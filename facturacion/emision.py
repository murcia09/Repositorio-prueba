"""Emisión de facturas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Venta:
    """Representa una venta del dominio."""

    identificador: str


@dataclass(frozen=True)
class Factura:
    """Representa la factura emitida para una venta."""

    identificador_venta: str
    estado: str = "emitida"


def emitir(venta: Venta) -> Factura:
    """Procesa una venta y devuelve su factura emitida.

    La operación es síncrona y de costo constante para minimizar latencia.
    """

    identificador_venta = getattr(venta, "identificador", None)
    if not identificador_venta:
        raise ValueError("La venta debe tener un identificador válido")

    return Factura(identificador_venta=identificador_venta)
