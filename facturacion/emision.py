"""Operación pública para emitir facturas a partir de una venta.

Incluye emisión normal y modo de contingencia:
- si no hay conectividad o falla el servicio tributario, la venta se guarda en cola;
- cuando vuelve la conectividad, las facturas pendientes se sincronizan automáticamente.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


class VentaInvalida(ValueError):
    """Señala que la venta no cumple el contrato mínimo esperado."""


class SincronizacionInvalida(ValueError):
    """Señala problemas al trabajar con la cola o el servicio tributario."""


def _validar_venta(venta: Dict[str, Any]) -> None:
    if not isinstance(venta, dict):
        raise VentaInvalida("La venta debe ser un diccionario.")

    if not venta.get("id_venta"):
        raise VentaInvalida("La venta debe incluir 'id_venta'.")

    if "total" not in venta or venta.get("total") is None:
        raise VentaInvalida("La venta debe incluir 'total'.")

    if venta.get("cliente") is not None and not isinstance(venta.get("cliente"), dict):
        raise VentaInvalida("'cliente' debe ser un diccionario cuando esté presente.")

    if venta.get("lineas") is not None and not isinstance(venta.get("lineas"), list):
        raise VentaInvalida("'lineas' debe ser una lista cuando esté presente.")


def _conectividad_disponible(verificador_conectividad) -> bool:
    """Obtiene el estado de conectividad desde el doble o adaptador provisto."""

    if verificador_conectividad is None:
        return True

    if hasattr(verificador_conectividad, "hay_conectividad"):
        return bool(verificador_conectividad.hay_conectividad())

    if callable(verificador_conectividad):
        return bool(verificador_conectividad())

    raise SincronizacionInvalida("El verificador de conectividad no expone una interfaz válida.")


def _enviar_al_servicio(servicio_tributario, venta: Dict[str, Any]) -> Dict[str, Any]:
    if servicio_tributario is None:
        return {"estado": "enviada", "id_venta": venta["id_venta"]}

    if hasattr(servicio_tributario, "enviar"):
        resultado = servicio_tributario.enviar(venta)
        if isinstance(resultado, dict):
            return resultado
        return {"estado": "enviada", "id_venta": venta["id_venta"], "respuesta": resultado}

    if callable(servicio_tributario):
        resultado = servicio_tributario(venta)
        if isinstance(resultado, dict):
            return resultado
        return {"estado": "enviada", "id_venta": venta["id_venta"], "respuesta": resultado}

    raise SincronizacionInvalida("El servicio tributario no expone una interfaz válida.")


def _guardar_en_cola(cola, venta: Dict[str, Any]) -> None:
    if cola is None or not hasattr(cola, "guardar"):
        raise SincronizacionInvalida("La cola no expone el método guardar(...).")
    cola.guardar(venta)


def _obtener_pendientes(cola) -> List[Dict[str, Any]]:
    if cola is None or not hasattr(cola, "pendientes"):
        raise SincronizacionInvalida("La cola no expone el método pendientes().")
    pendientes = cola.pendientes()
    if pendientes is None:
        return []
    return list(pendientes)


def _marcar_sincronizada(cola, venta: Dict[str, Any]) -> None:
    if cola is None or not hasattr(cola, "marcar_sincronizada"):
        raise SincronizacionInvalida("La cola no expone el método marcar_sincronizada(...).")
    cola.marcar_sincronizada(venta)


def emitir(venta: dict, *, verificador_conectividad=None, servicio_tributario=None, cola=None) -> dict:
    """Emite una factura observable a partir de una venta válida.

    Si no hay conectividad o el servicio tributario falla, la venta se guarda
    en cola y el resultado indica modo contingencia.
    """

    _validar_venta(venta)

    factura = deepcopy(venta)
    factura["fecha_emision"] = datetime.now(timezone.utc).isoformat()

    if not _conectividad_disponible(verificador_conectividad):
        _guardar_en_cola(cola, deepcopy(venta))
        factura["estado"] = "contingencia"
        factura["pendiente_sincronizacion"] = True
        return factura

    try:
        resultado_servicio = _enviar_al_servicio(servicio_tributario, venta)
    except Exception:
        _guardar_en_cola(cola, deepcopy(venta))
        factura["estado"] = "contingencia"
        factura["pendiente_sincronizacion"] = True
        return factura

    factura.update(resultado_servicio)
    factura.setdefault("id_venta", venta["id_venta"])
    factura["emitida"] = True
    factura["estado"] = resultado_servicio.get("estado", "emitida")
    factura["pendiente_sincronizacion"] = False
    return factura


def sincronizar_pendientes(*, cola, verificador_conectividad, servicio_tributario) -> dict:
    """Sincroniza las facturas pendientes cuando vuelve la conectividad."""

    pendientes = _obtener_pendientes(cola)
    if not _conectividad_disponible(verificador_conectividad):
        return {"sincronizadas": 0, "pendientes": pendientes}

    sincronizadas = 0
    pendientes_restantes: List[Dict[str, Any]] = []

    for venta in pendientes:
        if isinstance(venta, dict) and venta.get("estado_sync") == "sincronizada":
            pendientes_restantes.append(venta)
            continue

        try:
            _enviar_al_servicio(servicio_tributario, venta)
        except Exception:
            pendientes_restantes.append(venta)
            continue

        _marcar_sincronizada(cola, venta)
        sincronizadas += 1

    return {"sincronizadas": sincronizadas, "pendientes": pendientes_restantes}
