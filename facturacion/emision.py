"""Operación de emisión de facturas."""

from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class _Correo(Protocol):
    def enviar(self, destinatario: str, *, pdf: Any, xml: Any) -> Any:
        """Envía el comprobante por correo."""


def emitir(
    venta: dict,
    *,
    generador_pdf: Any = None,
    generador_xml: Any = None,
    correo: Any = None,
) -> dict:
    """Emite una factura asociada a una venta válida.

    Parameters
    ----------
    venta:
        Diccionario que debe contener al menos la clave ``venta_id``.
    generador_pdf:
        Objeto callable que recibe ``venta`` y devuelve el PDF visual.
    generador_xml:
        Objeto callable que recibe ``venta`` y devuelve el XML firmado.
    correo:
        Objeto con método ``enviar(destinatario, *, pdf, xml)``.

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

    factura = {"estado": "emitida", "venta_id": venta_id}

    if generador_pdf is None and generador_xml is None and correo is None:
        return factura

    if venta.get("pagada") is not True:
        raise ValueError("la venta debe estar pagada para enviar comprobante")

    correo_cliente = venta.get("correo_cliente")
    if not isinstance(correo_cliente, str) or not correo_cliente.strip():
        raise ValueError("correo_cliente debe ser una cadena no vacía")

    if generador_pdf is None or generador_xml is None or correo is None:
        raise ValueError("se requieren generador_pdf, generador_xml y correo")

    pdf = generador_pdf(venta)
    xml = generador_xml(venta)
    correo.enviar(correo_cliente, pdf=pdf, xml=xml)

    return factura
