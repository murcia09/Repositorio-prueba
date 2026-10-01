"""Operación de emisión de facturas."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


def emitir(
    venta: dict,
    *,
    servicio_tributario: Any | None = None,
    cola_contingencia: Any | None = None,
) -> dict:
    """Emite una factura asociada a una venta válida.

    Si se recibe ``servicio_tributario``, se intenta delegar la emisión en su
    método ``emitir(venta)``. Si ese colaborador falla por un problema de
    conexión o disponibilidad, la venta se guarda en ``cola_contingencia`` y se
    devuelve una factura en estado ``contingencia``.

    Parameters
    ----------
    venta:
        Diccionario que debe contener al menos la clave ``venta_id``.
    servicio_tributario:
        Colaborador opcional con método ``emitir(venta)``.
    cola_contingencia:
        Colaborador opcional con método ``guardar(item)`` para almacenar ventas
        pendientes cuando falla la emisión.

    Returns
    -------
    dict
        Factura emitida con estado ``"emitida"`` o ``"contingencia"``.

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

    if servicio_tributario is None:
        return {"estado": "emitida", "venta_id": venta_id}

    try:
        factura = servicio_tributario.emitir(venta)
    except (ConnectionError, TimeoutError, OSError):
        if cola_contingencia is not None:
            cola_contingencia.guardar(venta)
        return {"estado": "contingencia", "venta_id": venta_id}

    if not isinstance(factura, dict):
        factura = {"estado": "emitida", "venta_id": venta_id}
    else:
        factura = dict(factura)
        factura.setdefault("estado", "emitida")
        factura.setdefault("venta_id", venta_id)

    return factura


def sincronizar_pendientes(cola_contingencia, *, azure) -> int:
    """Sincroniza las facturas pendientes con Azure.

    Lee los pendientes desde ``cola_contingencia.obtener_pendientes()`` y los
    envía uno a uno mediante ``azure.enviar(factura)``. Si todo termina bien,
    limpia la cola mediante ``cola_contingencia.limpiar()`` y devuelve la
    cantidad de facturas sincronizadas.
    """

    pendientes = cola_contingencia.obtener_pendientes()
    sincronizadas = 0

    for factura in pendientes:
        azure.enviar(factura)
        sincronizadas += 1

    cola_contingencia.limpiar()
    return sincronizadas
