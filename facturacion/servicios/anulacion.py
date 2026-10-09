"""Anulacion de facturas timbradas, dentro del plazo legal.

Anular cancela el timbre ante el servicio de impuestos, devuelve las existencias al
inventario y deja la factura en estado anulada con su motivo. Una factura anulada
no se borra: el folio ya se uso y tiene que seguir existiendo.
"""

from __future__ import annotations

from facturacion.config import Configuracion
from facturacion.errores import EstadoInvalido, FacturaInvalida
from facturacion.integraciones.servicio_impuestos import ClienteServicioImpuestos
from facturacion.modelos import EstadoFactura, Factura
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.inventario import ServicioInventario
from facturacion.utilidades.fechas import dias_transcurridos

ESTADOS_ANULABLES = (EstadoFactura.TIMBRADA, EstadoFactura.PAGADA)


class ServicioAnulacion:
    def __init__(
        self,
        facturas: RepositorioFacturas,
        inventario: ServicioInventario,
        servicio_impuestos: ClienteServicioImpuestos,
        auditoria: RegistroAuditoria,
        config: Configuracion,
    ) -> None:
        self._facturas = facturas
        self._inventario = inventario
        self._impuestos = servicio_impuestos
        self._auditoria = auditoria
        self._config = config

    def anular(self, identificador: str, motivo: str) -> Factura:
        if not motivo.strip():
            raise FacturaInvalida("Para anular una factura hay que indicar el motivo.")
        factura = self._facturas.obtener_factura(identificador)
        if factura.estado == EstadoFactura.ANULADA:
            raise EstadoInvalido(f"La factura {identificador} ya estaba anulada.")
        if factura.estado not in ESTADOS_ANULABLES or factura.timbre is None:
            raise EstadoInvalido(
                f"Solo se anula una factura timbrada; {identificador} esta {factura.estado.value}."
            )
        if factura.fecha_emision and (
            dias_transcurridos(factura.fecha_emision) > self._config.dias_maximos_anulacion
        ):
            raise EstadoInvalido(
                f"La factura {identificador} supera el plazo de "
                f"{self._config.dias_maximos_anulacion} dias para anularse: emite una nota credito."
            )
        self._impuestos.cancelar(factura.timbre.uuid)
        self._inventario.liberar(factura.lineas)
        factura.estado = EstadoFactura.ANULADA
        factura.motivo_anulacion = motivo
        self._facturas.guardar_factura(factura)
        self._auditoria.registrar("factura_anulada", factura=identificador, motivo=motivo)
        return factura
