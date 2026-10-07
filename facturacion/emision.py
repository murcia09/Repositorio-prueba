"""Emisión de facturas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Venta:
    """Representa una venta del dominio."""

    identificador: str
    correo: str | None = None
    pagada: bool = False


@dataclass(frozen=True)
class Factura:
    """Representa la factura emitida para una venta."""

    identificador_venta: str
    estado: str = "emitida"


def _obtener_atributo(objeto: Any, nombre: str, defecto: Any = None) -> Any:
    return getattr(objeto, nombre, defecto)


def _validar_venta_pagada(venta: Any) -> tuple[str, str | None]:
    identificador = _obtener_atributo(venta, "identificador")
    if not identificador:
        raise ValueError("La venta debe tener un identificador válido")

    pagada = _obtener_atributo(venta, "pagada", False)
    if not pagada:
        raise ValueError("La venta debe estar pagada para emitir la factura")

    correo = _obtener_atributo(venta, "correo")
    if not correo:
        raise ValueError("La venta debe tener un correo de cliente válido")

    return identificador, correo


def _nombre_artefacto(identificador: str, sufijo: str) -> str:
    return f"{identificador}-{sufijo}"


def _adjuntos_para_correo(pdf: Any, xml: Any) -> list[Any]:
    return [pdf, xml]


def emitir(
    venta: Venta,
    *,
    generador_pdf=None,
    generador_xml=None,
    almacen=None,
    correo=None,
) -> Factura:
    """Procesa una venta y devuelve su factura emitida.

    Si se proporcionan colaboradores, genera el PDF y el XML, los almacena
    y los envía por correo al cliente.
    """

    identificador = _obtener_atributo(venta, "identificador")
    if not identificador:
        raise ValueError("La venta debe tener un identificador válido")

    if all(colaborador is None for colaborador in (generador_pdf, generador_xml, almacen, correo)):
        return Factura(identificador_venta=identificador)

    identificador, destinatario = _validar_venta_pagada(venta)

    if generador_pdf is None or generador_xml is None or almacen is None or correo is None:
        raise ValueError("Se requieren generadores, almacenamiento y correo para procesar la venta pagada")

    pdf = generador_pdf(venta)
    xml = generador_xml(venta)

    almacen.guardar(_nombre_artefacto(identificador, "pdf"), pdf)
    almacen.guardar(_nombre_artefacto(identificador, "xml"), xml)

    correo.enviar(destinatario, adjuntos=_adjuntos_para_correo(pdf, xml))

    return Factura(identificador_venta=identificador)
