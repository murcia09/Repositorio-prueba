"""Devoluciones de mercancia sobre una factura timbrada.

Una devolucion no anula la factura: genera una nota credito por lo devuelto y
reingresa las unidades al inventario. Solo se puede devolver lo que se vendio, y no
mas de una vez.
"""

from __future__ import annotations

from dataclasses import dataclass

from facturacion.errores import FacturaInvalida
from facturacion.modelos import LineaFactura, NotaCredito
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.calculos import importe_neto, impuesto_linea
from facturacion.servicios.inventario import ServicioInventario
from facturacion.servicios.notas_credito import ServicioNotasCredito
from facturacion.utilidades.dinero import sumar


@dataclass(frozen=True)
class ItemDevuelto:
    codigo: str
    cantidad: int


class ServicioDevoluciones:
    def __init__(
        self,
        facturas: RepositorioFacturas,
        inventario: ServicioInventario,
        notas_credito: ServicioNotasCredito,
        auditoria: RegistroAuditoria,
    ) -> None:
        self._facturas = facturas
        self._inventario = inventario
        self._notas = notas_credito
        self._auditoria = auditoria
        self._devuelto: dict[tuple[str, str], int] = {}

    def devolver(self, identificador: str, items: list[ItemDevuelto], motivo: str) -> NotaCredito:
        factura = self._facturas.obtener_factura(identificador)
        vendidas = {linea.producto.codigo: linea for linea in factura.lineas}
        lineas_devueltas: list[LineaFactura] = []
        for item in items:
            linea = vendidas.get(item.codigo)
            if linea is None:
                raise FacturaInvalida(f"{item.codigo} no esta en la factura {identificador}.")
            ya = self._devuelto.get((identificador, item.codigo), 0)
            if item.cantidad <= 0 or ya + item.cantidad > linea.cantidad:
                raise FacturaInvalida(
                    f"No se pueden devolver {item.cantidad} de {item.codigo}: se vendieron "
                    f"{linea.cantidad} y ya se devolvieron {ya}."
                )
            # El descuento se reparte en proporcion a lo devuelto.
            proporcion = linea.descuento * item.cantidad / linea.cantidad
            lineas_devueltas.append(LineaFactura(linea.producto, item.cantidad, proporcion))

        monto = sumar(importe_neto(l) + impuesto_linea(l) for l in lineas_devueltas)
        nota = self._notas.emitir(factura, monto, motivo)
        self._inventario.liberar(lineas_devueltas)
        for item in items:
            clave = (identificador, item.codigo)
            self._devuelto[clave] = self._devuelto.get(clave, 0) + item.cantidad
        self._auditoria.registrar(
            "devolucion", factura=identificador, nota=f"{nota.serie}-{nota.folio}", monto=str(monto)
        )
        return nota
