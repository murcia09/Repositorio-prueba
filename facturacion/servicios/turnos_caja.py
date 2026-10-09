"""Turnos de caja: apertura con base, movimientos de efectivo y cierre con arqueo.

El arqueo compara el efectivo que deberia haber (base + ventas en efectivo +
ingresos - retiros) con el que el cajero cuenta. La diferencia queda registrada:
no se corrige sola, la revisa el supervisor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from facturacion.errores import EstadoInvalido, PagoRechazado
from facturacion.modelos import MedioPago
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.utilidades.dinero import a_decimal, redondear, sumar
from facturacion.utilidades.fechas import ahora


@dataclass
class Movimiento:
    tipo: str  # "ingreso" o "retiro"
    monto: Decimal
    motivo: str
    fecha: datetime


@dataclass
class Turno:
    cajero_id: str
    base: Decimal
    apertura: datetime
    cierre: datetime | None = None
    movimientos: list[Movimiento] = field(default_factory=list)
    contado: Decimal | None = None
    diferencia: Decimal | None = None

    @property
    def abierto(self) -> bool:
        return self.cierre is None


class ServicioTurnos:
    def __init__(self, facturas: RepositorioFacturas, auditoria: RegistroAuditoria) -> None:
        self._facturas = facturas
        self._auditoria = auditoria
        self._turnos: dict[str, Turno] = {}

    def abrir(self, cajero_id: str, base: object) -> Turno:
        actual = self._turnos.get(cajero_id)
        if actual and actual.abierto:
            raise EstadoInvalido(f"El cajero {cajero_id} ya tiene un turno abierto.")
        turno = Turno(cajero_id, redondear(base), ahora())
        self._turnos[cajero_id] = turno
        self._auditoria.registrar("turno_abierto", cajero=cajero_id, base=str(turno.base))
        return turno

    def turno_abierto(self, cajero_id: str) -> Turno:
        turno = self._turnos.get(cajero_id)
        if turno is None or not turno.abierto:
            raise EstadoInvalido(f"El cajero {cajero_id} no tiene un turno abierto.")
        return turno

    def registrar_movimiento(self, cajero_id: str, tipo: str, monto: object, motivo: str) -> Movimiento:
        if tipo not in ("ingreso", "retiro"):
            raise PagoRechazado("Un movimiento de caja es 'ingreso' o 'retiro'.")
        valor = redondear(a_decimal(monto))
        if valor <= 0:
            raise PagoRechazado("El monto del movimiento debe ser mayor que cero.")
        turno = self.turno_abierto(cajero_id)
        movimiento = Movimiento(tipo, valor, motivo, ahora())
        turno.movimientos.append(movimiento)
        return movimiento

    def efectivo_esperado(self, turno: Turno) -> Decimal:
        ventas = sumar(
            pago.monto
            for factura in self._facturas.listar()
            for pago in factura.pagos
            if pago.medio == MedioPago.EFECTIVO and pago.fecha >= turno.apertura
        )
        ingresos = sumar(m.monto for m in turno.movimientos if m.tipo == "ingreso")
        retiros = sumar(m.monto for m in turno.movimientos if m.tipo == "retiro")
        return redondear(turno.base + ventas + ingresos - retiros)

    def cerrar(self, cajero_id: str, contado: object) -> Turno:
        turno = self.turno_abierto(cajero_id)
        turno.contado = redondear(contado)
        turno.diferencia = redondear(turno.contado - self.efectivo_esperado(turno))
        turno.cierre = ahora()
        self._auditoria.registrar(
            "turno_cerrado", cajero=cajero_id, contado=str(turno.contado), diferencia=str(turno.diferencia)
        )
        return turno
