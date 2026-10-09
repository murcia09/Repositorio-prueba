"""Lógica de emisión de facturas."""

from __future__ import annotations

from typing import Any


def emitir(solicitud: Any, *, timbrador: Any) -> Any:
    """Emite una factura delegando el timbrado al colaborador inyectado.

    Parameters
    ----------
    solicitud:
        Solicitud de factura que se pasará sin modificar al timbrador.
    timbrador:
        Colaborador que debe exponer un método ``timbrar`` y devolver la factura
        timbrada.

    Returns
    -------
    Any
        La factura timbrada producida por ``timbrador.timbrar(solicitud)``.
    """

    return timbrador.timbrar(solicitud)
