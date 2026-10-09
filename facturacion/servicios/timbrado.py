"""Timbrado: el servicio de impuestos valida la factura y le pone su sello.

Hasta que no se timbra, una factura no tiene validez fiscal y no se puede cobrar.
Si el servicio no responde, se reintenta hasta `reintentos_timbrado` veces; si
sigue sin responder, la factura queda emitida y el timbrado falla con
ErrorTimbrado. Hoy no hay modo de contingencia: sin servicio de impuestos no se
puede facturar.
"""

from __future__ import annotations

from facturacion.config import Configuracion
from facturacion.documentos.xml import generar_xml
from facturacion.errores import ErrorTimbrado, EstadoInvalido, ServicioImpuestosNoDisponible
from facturacion.integraciones.servicio_impuestos import ClienteServicioImpuestos
from facturacion.modelos import EstadoFactura, Factura
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria


class ServicioTimbrado:
    def __init__(
        self,
        servicio_impuestos: ClienteServicioImpuestos,
        facturas: RepositorioFacturas,
        auditoria: RegistroAuditoria,
        config: Configuracion,
    ) -> None:
        self._impuestos = servicio_impuestos
        self._facturas = facturas
        self._auditoria = auditoria
        self._config = config

    def timbrar(self, factura: Factura) -> Factura:
        if factura.estado != EstadoFactura.EMITIDA:
            raise EstadoInvalido(
                f"Solo se timbra una factura emitida; {factura.identificador} esta "
                f"{factura.estado.value}."
            )
        xml = generar_xml(factura, self._config)
        ultimo_error: Exception | None = None
        for intento in range(1, self._config.reintentos_timbrado + 1):
            try:
                timbre = self._impuestos.timbrar(xml, timeout_s=self._config.timeout_timbrado_s)
            except (ServicioImpuestosNoDisponible, TimeoutError) as exc:
                ultimo_error = exc
                self._auditoria.registrar(
                    "timbrado_fallido", factura=factura.identificador, intento=intento, error=str(exc)
                )
                continue
            factura.timbre = timbre
            factura.estado = EstadoFactura.TIMBRADA
            self._facturas.guardar_factura(factura)
            self._auditoria.registrar(
                "factura_timbrada", factura=factura.identificador, uuid=timbre.uuid, intento=intento
            )
            return factura
        raise ErrorTimbrado(
            f"No se pudo timbrar {factura.identificador} tras "
            f"{self._config.reintentos_timbrado} intentos: {ultimo_error}"
        )
