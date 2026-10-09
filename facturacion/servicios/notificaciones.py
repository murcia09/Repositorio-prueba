"""Avisos por correo al cliente.

Hoy solo existe el aviso de factura anulada. El envio del comprobante (PDF y XML)
al comprador todavia no esta implementado.
"""

from __future__ import annotations

from facturacion.config import Configuracion
from facturacion.errores import ErrorCorreo
from facturacion.integraciones.correo import ClienteCorreo
from facturacion.modelos import Factura
from facturacion.utilidades.validaciones import validar_correo


class ServicioNotificaciones:
    def __init__(self, correo: ClienteCorreo, config: Configuracion) -> None:
        self._correo = correo
        self._config = config

    def enviar(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        adjuntos: dict[str, bytes] | None = None,
    ) -> None:
        if not validar_correo(destinatario):
            raise ErrorCorreo(f"El destinatario {destinatario} no es un correo valido.")
        self._correo.enviar(
            remitente=self._config.remitente_correo,
            destinatario=destinatario,
            asunto=asunto,
            cuerpo=cuerpo,
            adjuntos=adjuntos or {},
        )

    def avisar_anulacion(self, factura: Factura) -> bool:
        """Avisa al cliente de que su factura se anulo. False si no tiene correo."""
        if not factura.cliente.correo:
            return False
        self.enviar(
            factura.cliente.correo,
            f"Factura {factura.identificador} anulada",
            f"Hola {factura.cliente.nombre}: su factura {factura.identificador} fue anulada. "
            f"Motivo: {factura.motivo_anulacion}.",
        )
        return True
