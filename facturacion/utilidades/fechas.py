"""Fechas siempre con zona horaria: una factura sin zona es ambigua para el fisco."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

ZONA_COLOMBIA = timezone(timedelta(hours=-5), name="America/Bogota")


def ahora() -> datetime:
    return datetime.now(ZONA_COLOMBIA)


def dias_transcurridos(desde: datetime, hasta: datetime | None = None) -> int:
    """Dias completos entre dos momentos. Sin `hasta`, hasta ahora."""
    return ((hasta or ahora()) - desde).days


def inicio_del_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min, tzinfo=ZONA_COLOMBIA)


def fin_del_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.max, tzinfo=ZONA_COLOMBIA)


def formato_iso(momento: datetime) -> str:
    """`2026-10-09T10:15:00-05:00`, el formato que espera el servicio de impuestos."""
    return momento.isoformat(timespec="seconds")
