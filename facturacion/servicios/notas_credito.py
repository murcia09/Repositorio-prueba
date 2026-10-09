"""Notas credito: devolucion parcial o total sobre una factura ya timbrada.

Es lo que se usa cuando ya paso el plazo para anular, o cuando solo se devuelve una
parte de la compra. La suma de las notas de una factura nunca supera su total.
"""

from __future__ import annotations

from decimal import Decimal

from facturacion.errores import EstadoInvalido, FacturaInvalida
from facturacion.modelos import EstadoFactura, Factura, NotaCredito
from facturacion.repositorios.memoria import RepositorioNotasCredito
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.numeracion import GeneradorFolios
from facturacion.utilidades.dinero import a_decimal, redondear, sumar
from facturacion.utilidades.fechas import ahora


class ServicioNotasCredito:
    def __init__(
        self,
        notas: RepositorioNotasCredito,
        folios: GeneradorFolios,
        auditoria: RegistroAuditoria,
    ) -> None:
        self._notas = notas
        self._folios = folios
        self._auditoria = auditoria

    def acreditado(self, factura: Factura) -> Decimal:
        return sumar(n.monto for n in self._notas.de_factura(factura.identificador))

    def emitir(self, factura: Factura, monto: object, motivo: str) -> NotaCredito:
        if factura.estado not in (EstadoFactura.TIMBRADA, EstadoFactura.PAGADA):
            raise EstadoInvalido(
                f"Solo se acredita una factura timbrada; {factura.identificador} esta "
                f"{factura.estado.value}."
            )
        valor = redondear(a_decimal(monto))
        if valor <= 0:
            raise FacturaInvalida("El monto de la nota credito debe ser mayor que cero.")
        if self.acreditado(factura) + valor > factura.total:
            raise FacturaInvalida(
                f"La nota credito supera lo que queda por acreditar de {factura.identificador}."
            )
        nota = NotaCredito(
            serie=self._folios.serie,
            folio=self._folios.siguiente(),
            factura_origen=factura.identificador,
            monto=valor,
            motivo=motivo,
            fecha=ahora(),
        )
        self._notas.guardar_nota(nota)
        self._auditoria.registrar(
            "nota_credito_emitida", factura=factura.identificador, nota=f"{nota.serie}-{nota.folio}",
            monto=str(valor),
        )
        return nota
