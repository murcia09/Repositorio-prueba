"""Exportacion de las ventas al sistema contable, en CSV.

Un asiento por factura: debito a caja o bancos segun el medio de pago, credito a
ingresos por el subtotal neto y credito a IVA por pagar por el impuesto. El
contador importa este archivo al cierre del mes.
"""

from __future__ import annotations

import csv
import io
from datetime import date

from facturacion.modelos import EstadoFactura, Factura, MedioPago
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.utilidades.dinero import redondear

CUENTA_CAJA = "110505"
CUENTA_BANCOS = "111005"
CUENTA_INGRESOS = "413524"
CUENTA_IVA = "240802"
CUENTA_CLIENTES = "130505"

COLUMNAS = ("fecha", "comprobante", "cuenta", "tercero", "debito", "credito")


def _cuenta_de_cobro(factura: Factura, medio: MedioPago) -> str:
    return CUENTA_CAJA if medio == MedioPago.EFECTIVO else CUENTA_BANCOS


def asientos(factura: Factura) -> list[dict[str, str]]:
    """Las lineas contables de una factura. Debitos y creditos siempre cuadran."""
    fecha = factura.fecha_emision.date().isoformat() if factura.fecha_emision else ""
    base = {"fecha": fecha, "comprobante": factura.identificador, "tercero": factura.cliente.nit}
    filas = []
    for pago in factura.pagos:
        filas.append({**base, "cuenta": _cuenta_de_cobro(factura, pago.medio),
                      "debito": str(pago.monto), "credito": "0"})
    if factura.saldo > 0:
        filas.append({**base, "cuenta": CUENTA_CLIENTES, "debito": str(factura.saldo), "credito": "0"})
    filas.append({**base, "cuenta": CUENTA_INGRESOS, "debito": "0",
                  "credito": str(redondear(factura.subtotal - factura.descuentos))})
    filas.append({**base, "cuenta": CUENTA_IVA, "debito": "0", "credito": str(factura.impuestos)})
    return filas


def exportar_csv(facturas: RepositorioFacturas, desde: date, hasta: date) -> str:
    """CSV con los asientos de las facturas timbradas o pagadas del periodo."""
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=COLUMNAS, lineterminator="\n")
    escritor.writeheader()
    for factura in sorted(facturas.listar(), key=lambda f: (f.serie, f.folio or 0)):
        if factura.estado not in (EstadoFactura.TIMBRADA, EstadoFactura.PAGADA):
            continue
        if factura.fecha_emision and desde <= factura.fecha_emision.date() <= hasta:
            escritor.writerows(asientos(factura))
    return salida.getvalue()
