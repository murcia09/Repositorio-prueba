"""Registro de operaciones: que paso, cuando y con que datos.

Requisito de control interno: toda emision, timbrado, pago y anulacion queda
registrada. Tambien se registran los fallos, como un timbrado que no respondio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from facturacion.utilidades.fechas import ahora


@dataclass(frozen=True)
class Evento:
    tipo: str
    fecha: datetime
    datos: dict[str, Any] = field(default_factory=dict)


class RegistroAuditoria:
    def __init__(self) -> None:
        self._eventos: list[Evento] = []

    def registrar(self, tipo: str, **datos: Any) -> Evento:
        evento = Evento(tipo, ahora(), dict(datos))
        self._eventos.append(evento)
        return evento

    def eventos(self, tipo: str | None = None) -> list[Evento]:
        return [e for e in self._eventos if tipo is None or e.tipo == tipo]

    def ultimo(self, tipo: str) -> Evento | None:
        encontrados = self.eventos(tipo)
        return encontrados[-1] if encontrados else None
