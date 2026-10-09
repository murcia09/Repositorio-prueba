"""Reportes de ventas para el cierre de caja y para el contador."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

from facturacion.modelos import EstadoFactura, Factura
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.calculos import desglose_impuestos
from facturacion.utilidades.dinero import redondear, sumar


def _validas(facturas: list[Factura]) -> list[Factura]:
    """Las anuladas y los borradores no cuentan como venta."""
    return [
        f for f in facturas if f.estado not in (EstadoFactura.ANULADA, EstadoFactura.BORRADOR)
    ]


def ventas_del_dia(facturas: RepositorioFacturas, dia: date) -> dict[str, object]:
    validas = _validas(facturas.del_dia(dia))
    return {
        "facturas": len(validas),
        "subtotal": sumar(f.subtotal for f in validas),
        "descuentos": sumar(f.descuentos for f in validas),
        "impuestos": sumar(f.impuestos for f in validas),
        "total": sumar(f.total for f in validas),
    }


def productos_mas_vendidos(facturas: RepositorioFacturas, limite: int = 5) -> list[tuple[str, int]]:
    """Los productos con mas unidades vendidas: [(codigo, unidades), ...]."""
    unidades: Counter[str] = Counter()
    for factura in _validas(facturas.listar()):
        for linea in factura.lineas:
            unidades[linea.producto.codigo] += linea.cantidad
    return unidades.most_common(limite)


def impuestos_por_tasa(facturas: RepositorioFacturas, desde: date, hasta: date) -> dict[Decimal, Decimal]:
    """IVA del periodo agrupado por tasa, para la declaracion."""
    por_tasa: dict[Decimal, Decimal] = defaultdict(lambda: Decimal("0"))
    for factura in _validas(facturas.listar()):
        if factura.fecha_emision and desde <= factura.fecha_emision.date() <= hasta:
            for tasa, valor in desglose_impuestos(factura).items():
                por_tasa[tasa] += valor
    return {tasa: redondear(valor) for tasa, valor in por_tasa.items()}


def cierre_de_caja(facturas: RepositorioFacturas, dia: date) -> dict[str, Decimal]:
    """Lo cobrado en el dia por medio de pago: lo que el cajero debe entregar."""
    por_medio: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for factura in _validas(facturas.del_dia(dia)):
        for pago in factura.pagos:
            por_medio[pago.medio.value] += pago.monto
    return {medio: redondear(valor) for medio, valor in por_medio.items()}
