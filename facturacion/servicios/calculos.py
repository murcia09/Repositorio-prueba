"""Calculo de importes, descuentos e impuestos de una factura.

Cada importe se redondea a centavos en el momento en que se calcula, linea por
linea, y los totales son la suma de esos importes ya redondeados. Es lo que hace el
servicio de impuestos al validar: si el total se calculara de otra forma, podria
diferir en un centavo y la factura se rechazaria.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from facturacion.errores import FacturaInvalida
from facturacion.modelos import Factura, LineaFactura
from facturacion.utilidades.dinero import a_decimal, porcentaje, redondear, sumar


def importe_bruto(linea: LineaFactura) -> Decimal:
    """Precio por cantidad, sin descuentos ni impuestos."""
    return redondear(linea.producto.precio_unitario * linea.cantidad)


def importe_neto(linea: LineaFactura) -> Decimal:
    """Importe de la linea despues del descuento, antes de impuestos."""
    neto = importe_bruto(linea) - a_decimal(linea.descuento)
    if neto < 0:
        raise FacturaInvalida(
            f"El descuento de {linea.producto.codigo} es mayor que el importe de la linea."
        )
    return redondear(neto)


def impuesto_linea(linea: LineaFactura) -> Decimal:
    """IVA de la linea: se calcula sobre el importe ya descontado."""
    return porcentaje(importe_neto(linea), linea.producto.tasa_iva)


def aplicar_descuento_porcentual(linea: LineaFactura, tasa: object) -> LineaFactura:
    """Devuelve la linea con un descuento del `tasa` (0.10 = 10 %) sobre su importe."""
    t = a_decimal(tasa)
    if not Decimal("0") <= t <= Decimal("1"):
        raise FacturaInvalida("El descuento debe estar entre 0 y 1.")
    return LineaFactura(linea.producto, linea.cantidad, porcentaje(importe_bruto(linea), t))


def desglose_impuestos(factura: Factura) -> dict[Decimal, Decimal]:
    """Impuesto total por cada tasa, como lo pide el XML: {0.19: 2375.00, 0: 0.00}."""
    por_tasa: dict[Decimal, Decimal] = defaultdict(lambda: Decimal("0"))
    for linea in factura.lineas:
        por_tasa[linea.producto.tasa_iva] += impuesto_linea(linea)
    return {tasa: redondear(valor) for tasa, valor in por_tasa.items()}


def calcular_totales(factura: Factura) -> Factura:
    """Rellena subtotal, descuentos, impuestos y total de la factura y la devuelve."""
    if not factura.lineas:
        raise FacturaInvalida("Una factura necesita al menos una linea.")
    factura.subtotal = sumar(importe_bruto(linea) for linea in factura.lineas)
    factura.descuentos = sumar(a_decimal(linea.descuento) for linea in factura.lineas)
    factura.impuestos = sumar(impuesto_linea(linea) for linea in factura.lineas)
    factura.total = redondear(factura.subtotal - factura.descuentos + factura.impuestos)
    return factura
