"""Promociones del punto de venta: porcentaje por producto, lleve N pague M y cupones.

Las promociones se aplican al carrito antes de emitir, convirtiendose en descuentos
de linea. Asi la factura y el XML muestran el descuento en cada concepto, que es
como lo pide el fisco, y no un descuento global sin desglose.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from facturacion.errores import FacturaInvalida
from facturacion.modelos import LineaFactura
from facturacion.servicios.calculos import importe_bruto
from facturacion.utilidades.dinero import a_decimal, porcentaje, redondear


@dataclass(frozen=True)
class PromocionPorcentaje:
    """Un porcentaje de descuento sobre ciertos productos, entre dos fechas."""

    nombre: str
    codigos: frozenset[str]
    tasa: Decimal
    desde: date
    hasta: date

    def vigente(self, dia: date) -> bool:
        return self.desde <= dia <= self.hasta


@dataclass(frozen=True)
class PromocionLleveNPagueM:
    """Lleve 3 pague 2: por cada `n` unidades, `n - m` salen gratis."""

    nombre: str
    codigo: str
    n: int
    m: int

    def __post_init__(self) -> None:
        if not 0 < self.m < self.n:
            raise ValueError("En 'lleve N pague M' tiene que cumplirse 0 < M < N.")


@dataclass(frozen=True)
class Cupon:
    codigo: str
    valor: Decimal
    usos_maximos: int = 1


class MotorPromociones:
    def __init__(self) -> None:
        self._porcentajes: list[PromocionPorcentaje] = []
        self._lleve: list[PromocionLleveNPagueM] = []
        self._cupones: dict[str, Cupon] = {}
        self._usos: dict[str, int] = {}

    def agregar_porcentaje(self, promocion: PromocionPorcentaje) -> None:
        self._porcentajes.append(promocion)

    def agregar_lleve_pague(self, promocion: PromocionLleveNPagueM) -> None:
        self._lleve.append(promocion)

    def agregar_cupon(self, cupon: Cupon) -> None:
        self._cupones[cupon.codigo.upper()] = cupon

    def _descuento_linea(self, linea: LineaFactura, dia: date) -> Decimal:
        bruto = importe_bruto(linea)
        mejor = Decimal("0")
        for promo in self._porcentajes:
            if promo.vigente(dia) and linea.producto.codigo in promo.codigos:
                mejor = max(mejor, porcentaje(bruto, promo.tasa))
        for promo in self._lleve:
            if promo.codigo == linea.producto.codigo:
                gratis = (linea.cantidad // promo.n) * (promo.n - promo.m)
                mejor = max(mejor, redondear(linea.producto.precio_unitario * gratis))
        # Las promociones no se acumulan: se aplica la mas favorable para el cliente.
        return min(mejor, bruto)

    def aplicar(self, lineas: list[LineaFactura], dia: date) -> list[LineaFactura]:
        """Devuelve el carrito con el descuento de la mejor promocion de cada linea."""
        return [
            LineaFactura(linea.producto, linea.cantidad, self._descuento_linea(linea, dia))
            for linea in lineas
        ]

    def redimir_cupon(self, codigo: str, lineas: list[LineaFactura]) -> list[LineaFactura]:
        """Reparte el valor del cupon entre las lineas, de la mas cara a la mas barata."""
        cupon = self._cupones.get(codigo.upper())
        if cupon is None:
            raise FacturaInvalida(f"El cupon {codigo} no existe.")
        if self._usos.get(cupon.codigo, 0) >= cupon.usos_maximos:
            raise FacturaInvalida(f"El cupon {codigo} ya se uso.")
        restante = a_decimal(cupon.valor)
        resultado = []
        for linea in sorted(lineas, key=importe_bruto, reverse=True):
            disponible = importe_bruto(linea) - a_decimal(linea.descuento)
            aplicado = min(restante, disponible)
            restante -= aplicado
            resultado.append(LineaFactura(linea.producto, linea.cantidad, linea.descuento + aplicado))
        self._usos[cupon.codigo] = self._usos.get(cupon.codigo, 0) + 1
        return resultado
