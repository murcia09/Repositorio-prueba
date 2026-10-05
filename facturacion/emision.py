"""Lógica de emisión de facturas y sincronización de contingencia."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional


Generador = Callable[[Dict[str, Any]], Any]
EnviadorCorreo = Callable[[str, str, str, list[Any]], Any]
Sincronizador = Callable[[Dict[str, Any]], Any]


def _obtener_email_cliente(venta: Dict[str, Any]) -> Optional[str]:
    cliente = venta.get("cliente")
    if isinstance(cliente, dict):
        email = cliente.get("email")
        if isinstance(email, str) and email.strip():
            return email
    return None


def emitir(
    venta: Dict[str, Any],
    *,
    generador_pdf: Optional[Generador] = None,
    generador_xml: Optional[Generador] = None,
    enviador_correo: Optional[EnviadorCorreo] = None,
) -> Dict[str, Any]:
    """Emite una factura o procesa el comprobante de una venta pagada.

    Compatibilidad:
    - Si no se proporcionan generadores ni enviador de correo, conserva el
      comportamiento histórico y devuelve una factura marcada como "emitida".
    - Si la venta está pagada y se proporcionan los colaboradores, genera el
      PDF y el XML, los envía por correo al cliente y devuelve un resultado
      observable del procesamiento.
    """
    if not isinstance(venta, dict):
        raise TypeError("venta debe ser un diccionario")

    if generador_pdf is None and generador_xml is None and enviador_correo is None:
        return {
            "estado": "emitida",
            "venta": deepcopy(venta),
        }

    if not venta.get("pagada", False):
        return {
            "estado": "pendiente",
            "venta": deepcopy(venta),
        }

    if generador_pdf is None or generador_xml is None or enviador_correo is None:
        raise TypeError(
            "se requieren generador_pdf, generador_xml y enviador_correo para procesar una venta pagada"
        )

    pdf_visual = generador_pdf(venta)
    xml_firmado = generador_xml(venta)

    destinatario = _obtener_email_cliente(venta)
    if destinatario is None:
        raise ValueError("la venta pagada debe incluir cliente.email válido")

    enviador_correo(
        destinatario,
        "",
        "",
        [pdf_visual, xml_firmado],
    )

    return {
        "estado": "procesada",
        "venta": deepcopy(venta),
    }


def sincronizar_facturas_pendientes(
    facturas_pendientes: List[Dict[str, Any]],
    *,
    sincronizador: Sincronizador,
) -> Dict[str, Any]:
    """Procesa la cola de facturas pendientes de sincronización.

    Llama al colaborador inyectado una vez por factura, en el mismo orden de
    entrada, y devuelve un resumen observable del proceso.
    """
    if not isinstance(facturas_pendientes, list):
        raise TypeError("facturas_pendientes debe ser una lista")

    procesadas_correctamente: List[Dict[str, Any]] = []
    fallidas: List[Dict[str, Any]] = []

    for factura in facturas_pendientes:
        factura_copia = deepcopy(factura)
        try:
            id_remoto = sincronizador(factura)
            if isinstance(factura_copia, dict):
                factura_copia["id_remoto"] = id_remoto
            procesadas_correctamente.append(factura_copia)
        except Exception as exc:  # pragma: no cover - se captura para resumir fallos
            fallidas.append(
                {
                    "factura": factura_copia,
                    "error": str(exc),
                }
            )

    return {
        "total_procesadas": len(facturas_pendientes),
        "procesadas_correctamente": procesadas_correctamente,
        "fallidas": fallidas,
    }
