"""Cliente del servicio de impuestos que timbra y cancela facturas.

En produccion es una API REST/JSON sobre HTTPS del proveedor autorizado por el
fisco. Aqui hay un contrato (`ClienteServicioImpuestos`) y una implementacion
simulada para desarrollo y pruebas, con latencia y fallos configurables.
"""

from __future__ import annotations

import hashlib
import time
from typing import Protocol
from uuid import uuid4

from facturacion.errores import ErrorTimbrado, ServicioImpuestosNoDisponible
from facturacion.modelos import Timbre
from facturacion.utilidades.fechas import ahora


class ClienteServicioImpuestos(Protocol):
    def timbrar(self, xml: str, *, timeout_s: float) -> Timbre:
        """Valida el XML y devuelve el timbre. Levanta ServicioImpuestosNoDisponible
        si el servicio no responde y TimeoutError si tarda mas que `timeout_s`."""
        ...

    def cancelar(self, uuid: str) -> None:
        """Anula ante el fisco una factura ya timbrada."""
        ...


class ServicioImpuestosSimulado:
    """Servicio de impuestos de mentira, para desarrollo y pruebas.

    - `latencia_s`: cuanto tarda en responder cada timbrado.
    - `disponible`: False simula que el servicio esta caido o que no hay internet.
    - `fallos_seguidos`: cuantas llamadas fallan antes de responder bien.
    """

    proveedor = "PROVEEDOR-SIMULADO"

    def __init__(self, latencia_s: float = 0.0, disponible: bool = True, fallos_seguidos: int = 0) -> None:
        self.latencia_s = latencia_s
        self.disponible = disponible
        self._fallos_pendientes = fallos_seguidos
        self.timbradas: dict[str, str] = {}
        self.canceladas: set[str] = set()
        self.llamadas = 0

    def timbrar(self, xml: str, *, timeout_s: float) -> Timbre:
        self.llamadas += 1
        if not self.disponible:
            raise ServicioImpuestosNoDisponible("El servicio de impuestos no responde.")
        if self._fallos_pendientes > 0:
            self._fallos_pendientes -= 1
            raise ServicioImpuestosNoDisponible("El servicio de impuestos devolvio un error temporal.")
        if self.latencia_s > timeout_s:
            raise TimeoutError(f"El servicio de impuestos tardo mas de {timeout_s} s.")
        if self.latencia_s:
            time.sleep(self.latencia_s)
        uuid = str(uuid4())
        self.timbradas[uuid] = xml
        return Timbre(
            uuid=uuid,
            sello=hashlib.sha256(xml.encode("utf-8")).hexdigest(),
            fecha=ahora(),
            proveedor=self.proveedor,
        )

    def cancelar(self, uuid: str) -> None:
        if not self.disponible:
            raise ServicioImpuestosNoDisponible("El servicio de impuestos no responde.")
        if uuid not in self.timbradas:
            raise ErrorTimbrado(f"El servicio de impuestos no conoce el UUID {uuid}.")
        self.canceladas.add(uuid)
