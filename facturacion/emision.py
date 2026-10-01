"""Lógica de emisión de facturas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
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


def _construir_factura_base(venta: Dict[str, Any]) -> Dict[str, Any]:
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


def _registrar_en_cola(cola_pendientes: Any, item: Dict[str, Any]) -> None:
    if cola_pendientes is None:
        return

    if hasattr(cola_pendientes, "registrar"):
        cola_pendientes.registrar(item)
        return

    if hasattr(cola_pendientes, "append"):
        cola_pendientes.append(item)
        return

    raise TypeError("La cola de pendientes debe exponer registrar() o append().")


def _resolver_llamable(colaborador: Any, nombre: str, metodo: str) -> Any:
    if colaborador is None:
        return None
    if hasattr(colaborador, metodo):
        return getattr(colaborador, metodo)
    if callable(colaborador):
        return colaborador
    raise TypeError(f"{nombre} debe ser callable o exponer {metodo}().")


def emitir(
    venta,
    *,
    verificador_conexion=None,
    procesador_tributario=None,
    cola_pendientes=None,
) -> Dict[str, Any]:
    """Emite una factura a partir de una venta válida.

    Si la conectividad o el servicio tributario fallan, la venta se registra
    en cola para sincronización posterior y se retorna un estado de contingencia.
    """

    _validar_venta(venta)

    verificador = _resolver_llamable(verificador_conexion, "verificador_conexion", "hay_conexion")
    procesador = _resolver_llamable(procesador_tributario, "procesador_tributario", "procesar")

    hay_conexion = True
    if verificador is not None:
        hay_conexion = bool(verificador())

    factura = _construir_factura_base(venta)

    if not hay_conexion:
        factura["estado"] = "contingencia"
        factura["pendiente_sincronizacion"] = True
        _registrar_en_cola(cola_pendientes, factura)
        return factura

    try:
        if procesador is not None:
            resultado = procesador(venta)
            if isinstance(resultado, dict):
                factura.update(resultado)
                factura.setdefault("estado", "emitida")
            else:
                factura["resultado_tributario"] = resultado
        return factura
    except Exception:
        factura["estado"] = "contingencia"
        factura["pendiente_sincronizacion"] = True
        _registrar_en_cola(cola_pendientes, factura)
        return factura


def sincronizar_pendientes(cola_pendientes, *, sincronizador) -> Dict[str, Any]:
    """Sincroniza una colección de facturas pendientes una por una."""

    if not (hasattr(sincronizador, "sincronizar") or callable(sincronizador)):
        raise TypeError("sincronizador debe ser callable o exponer sincronizar().")

    if cola_pendientes is None:
        pendientes: List[Dict[str, Any]] = []
    elif hasattr(cola_pendientes, "pendientes"):
        pendientes = list(cola_pendientes.pendientes)
    elif isinstance(cola_pendientes, list):
        pendientes = list(cola_pendientes)
    else:
        pendientes = list(cola_pendientes)

    sincronizadas = 0
    errores = []

    for factura in pendientes:
        try:
            if hasattr(sincronizador, "sincronizar"):
                sincronizador.sincronizar(factura)
            else:
                sincronizador(factura)
            sincronizadas += 1
        except Exception as exc:
            errores.append({"factura_id": factura.get("factura_id"), "error": str(exc)})

    return {
        "sincronizadas": sincronizadas,
        "pendientes_total": len(pendientes),
        "errores": errores,
    }
