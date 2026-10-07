"""Emisión de facturas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


def _validar_identificador(venta: Any) -> str:
    identificador = _obtener_atributo(venta, "identificador")
    if not identificador:
        raise ValueError("La venta debe tener un identificador válido")
    return identificador


def _validar_venta_pagada(venta: Any) -> tuple[str, str | None]:
    identificador = _validar_identificador(venta)

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


def _factura_contingencia(identificador: str) -> Factura:
    return Factura(identificador_venta=identificador, estado="contingencia")


def _guardar_en_cola(cola_contingencia: Any, venta_o_factura_pendiente: Any) -> None:
    if cola_contingencia is None:
        raise ValueError("Se requiere una cola de contingencia para registrar pendientes")

    guardar = getattr(cola_contingencia, "guardar", None)
    if not callable(guardar):
        raise ValueError("La cola de contingencia debe exponer guardar(...)")

    try:
        guardar(venta_o_factura_pendiente)
    except TypeError:
        guardar(venta_o_factura_pendiente,)


def emitir(
    venta: Venta,
    *,
    generador_pdf=None,
    generador_xml=None,
    almacen=None,
    correo=None,
    cliente_tributario=None,
    detector_conexion=None,
    cola_contingencia=None,
) -> Factura:
    """Procesa una venta y devuelve su factura emitida.

    Si se proporcionan colaboradores de facturación, genera el PDF y el XML,
    los almacena y los envía por correo al cliente.

    Si falla la conectividad o el cliente tributario, registra la venta en la
    cola de contingencia y devuelve la factura marcada como pendiente.
    """

    identificador = _validar_identificador(venta)

    if cliente_tributario is not None or detector_conexion is not None or cola_contingencia is not None:
        hay_red = True
        if callable(detector_conexion):
            hay_red = bool(detector_conexion())

        if not hay_red:
            _guardar_en_cola(cola_contingencia, venta)
            return _factura_contingencia(identificador)

        try:
            if callable(cliente_tributario):
                cliente_tributario(venta)
        except Exception:
            _guardar_en_cola(cola_contingencia, venta)
            return _factura_contingencia(identificador)

        return Factura(identificador_venta=identificador, estado="emitida")

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


def _obtener_pendientes(cola_contingencia: Any) -> list[Any]:
    if cola_contingencia is None:
        return []

    if hasattr(cola_contingencia, "obtener_pendientes") and callable(cola_contingencia.obtener_pendientes):
        return list(cola_contingencia.obtener_pendientes())

    pendientes = getattr(cola_contingencia, "pendientes", None)
    if pendientes is None:
        return []
    return list(pendientes)


def _eliminar_de_cola(cola_contingencia: Any, factura_pendiente: Any) -> None:
    eliminar = getattr(cola_contingencia, "eliminar", None)
    if callable(eliminar):
        eliminar(factura_pendiente)
        return

    pendientes = getattr(cola_contingencia, "pendientes", None)
    if isinstance(pendientes, list) and factura_pendiente in pendientes:
        pendientes.remove(factura_pendiente)


def sincronizar_pendientes(*, cola_contingencia, sincronizador_azure) -> int:
    """Sincroniza facturas pendientes y elimina de la cola las sincronizadas."""

    pendientes = _obtener_pendientes(cola_contingencia)
    procesadas = 0

    for factura_pendiente in pendientes:
        if sincronizador_azure(factura_pendiente):
            _eliminar_de_cola(cola_contingencia, factura_pendiente)
        procesadas += 1

    return procesadas
