"""Modelos del dominio: clientes, productos, facturas, pagos y notas de credito.

Son datos sin logica de negocio. Los calculos estan en servicios/calculos.py y las
reglas de cada operacion en su servicio: asi un modelo no cambia cada vez que
cambia una regla.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class EstadoFactura(str, Enum):
    """Ciclo de vida: borrador -> emitida -> timbrada -> pagada, o anulada."""

    BORRADOR = "borrador"
    EMITIDA = "emitida"
    TIMBRADA = "timbrada"
    PAGADA = "pagada"
    ANULADA = "anulada"


class MedioPago(str, Enum):
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"


@dataclass
class Cliente:
    id: str
    nombre: str
    nit: str
    correo: str | None = None


@dataclass
class Producto:
    codigo: str
    descripcion: str
    precio_unitario: Decimal
    tasa_iva: Decimal = Decimal("0.19")
    # Los servicios, como el envio a domicilio, no tienen existencias.
    controla_inventario: bool = True


@dataclass
class LineaFactura:
    producto: Producto
    cantidad: int
    # Descuento en dinero sobre el importe de la linea, no en porcentaje.
    descuento: Decimal = Decimal("0")


@dataclass
class Timbre:
    """Lo que devuelve el servicio de impuestos al timbrar: la prueba fiscal."""

    uuid: str
    sello: str
    fecha: datetime
    proveedor: str


@dataclass
class Pago:
    medio: MedioPago
    monto: Decimal
    fecha: datetime
    referencia: str | None = None


@dataclass
class Factura:
    serie: str
    cliente: Cliente
    lineas: list[LineaFactura] = field(default_factory=list)
    folio: int | None = None
    estado: EstadoFactura = EstadoFactura.BORRADOR
    subtotal: Decimal = Decimal("0")
    descuentos: Decimal = Decimal("0")
    impuestos: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    fecha_emision: datetime | None = None
    timbre: Timbre | None = None
    pagos: list[Pago] = field(default_factory=list)
    motivo_anulacion: str | None = None

    @property
    def identificador(self) -> str:
        """`FV-15`: serie y folio. Solo existe desde que la factura se emite."""
        if self.folio is None:
            raise ValueError("La factura todavia no tiene folio: no se ha emitido.")
        return f"{self.serie}-{self.folio}"

    @property
    def total_pagado(self) -> Decimal:
        return sum((p.monto for p in self.pagos), Decimal("0"))

    @property
    def saldo(self) -> Decimal:
        return max(self.total - self.total_pagado, Decimal("0"))


@dataclass
class NotaCredito:
    serie: str
    folio: int
    factura_origen: str
    monto: Decimal
    motivo: str
    fecha: datetime
