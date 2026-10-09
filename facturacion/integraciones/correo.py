"""Envio de correo.

En produccion es un proveedor de correo con API sobre HTTPS; aqui, una bandeja en
memoria que guarda lo enviado para poder comprobarlo en las pruebas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from facturacion.errores import ErrorCorreo


@dataclass
class Mensaje:
    remitente: str
    destinatario: str
    asunto: str
    cuerpo: str
    adjuntos: dict[str, bytes] = field(default_factory=dict)


class ClienteCorreo(Protocol):
    def enviar(
        self,
        *,
        remitente: str,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        adjuntos: dict[str, bytes],
    ) -> None: ...


class CorreoEnMemoria:
    """Bandeja de salida en memoria. Con `falla=True` simula un servidor caido."""

    def __init__(self, falla: bool = False) -> None:
        self.falla = falla
        self.enviados: list[Mensaje] = []

    def enviar(
        self,
        *,
        remitente: str,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        adjuntos: dict[str, bytes],
    ) -> None:
        if self.falla:
            raise ErrorCorreo("El servidor de correo no responde.")
        self.enviados.append(Mensaje(remitente, destinatario, asunto, cuerpo, dict(adjuntos)))
