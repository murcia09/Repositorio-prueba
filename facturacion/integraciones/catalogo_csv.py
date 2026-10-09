"""Carga del catalogo de productos desde un CSV del proveedor del sistema.

Columnas: codigo, descripcion, precio, iva, existencias, servicio. Las filas con
errores no detienen la carga: se reportan con su numero de linea y se sigue.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from facturacion.modelos import Producto
from facturacion.servicios.inventario import ServicioInventario

COLUMNAS_OBLIGATORIAS = ("codigo", "descripcion", "precio")


@dataclass
class ResultadoCarga:
    cargados: int = 0
    errores: list[str] = field(default_factory=list)


def _decimal(texto: str, campo: str) -> Decimal:
    try:
        return Decimal(texto.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"{campo} no es un numero: {texto!r}") from exc


def cargar_catalogo(texto_csv: str, inventario: ServicioInventario) -> ResultadoCarga:
    lector = csv.DictReader(io.StringIO(texto_csv))
    faltan = [c for c in COLUMNAS_OBLIGATORIAS if c not in (lector.fieldnames or [])]
    resultado = ResultadoCarga()
    if faltan:
        resultado.errores.append(f"Faltan columnas obligatorias: {', '.join(faltan)}.")
        return resultado
    for numero, fila in enumerate(lector, start=2):
        try:
            codigo = (fila.get("codigo") or "").strip().upper()
            if not codigo:
                raise ValueError("el codigo esta vacio")
            precio = _decimal(fila["precio"], "precio")
            if precio <= 0:
                raise ValueError("el precio debe ser mayor que cero")
            iva = _decimal(fila.get("iva") or "0.19", "iva")
            servicio = (fila.get("servicio") or "").strip().lower() in ("si", "s", "true", "1")
            existencias = int(fila.get("existencias") or 0)
            producto = Producto(codigo, fila["descripcion"].strip(), precio, iva, not servicio)
            inventario.registrar_producto(producto, existencias)
            resultado.cargados += 1
        except (ValueError, KeyError) as exc:
            resultado.errores.append(f"Linea {numero}: {exc}")
    return resultado
