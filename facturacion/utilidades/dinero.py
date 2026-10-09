"""Operaciones con dinero. Siempre Decimal y redondeo a centavos, nunca float.

Un float no representa 0,10 exactamente, y en una factura un centavo de diferencia
entre el total y la suma de las lineas basta para que el servicio de impuestos la
rechace.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

CENTAVOS = Decimal("0.01")


def a_decimal(valor: object) -> Decimal:
    """Convierte un numero o texto a Decimal sin pasar por la representacion binaria."""
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, float):
        # str() evita los errores binarios de float: 0.1 -> "0.1".
        return Decimal(str(valor))
    return Decimal(valor)


def redondear(valor: object) -> Decimal:
    """Redondeo comercial a dos decimales: 0,005 sube a 0,01."""
    return a_decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def sumar(valores: Iterable[object]) -> Decimal:
    return redondear(sum((a_decimal(v) for v in valores), Decimal("0")))


def porcentaje(valor: object, tasa: object) -> Decimal:
    """`porcentaje(1000, 0.19)` -> 190.00."""
    return redondear(a_decimal(valor) * a_decimal(tasa))


def formatear(valor: object, simbolo: str = "$") -> str:
    """Formato colombiano: punto de miles y coma decimal, `$ 1.234,50`."""
    v = redondear(valor)
    entero, _, decimales = f"{v:,.2f}".partition(".")
    return f"{simbolo} {entero.replace(',', '.')},{decimales}"
