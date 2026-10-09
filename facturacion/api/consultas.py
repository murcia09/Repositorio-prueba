"""Consultas de facturas: para el cajero, el supervisor y el contador."""

from __future__ import annotations

from datetime import date

from facturacion.aplicacion import Aplicacion
from facturacion.documentos.pdf import generar_pdf
from facturacion.documentos.xml import generar_xml
from facturacion.errores import EstadoInvalido
from facturacion.modelos import Factura
from facturacion.seguridad.autenticacion import Usuario, exigir_rol
from facturacion.servicios import reportes


class ConsultaFacturas:
    def __init__(self, app: Aplicacion, usuario: Usuario) -> None:
        exigir_rol(usuario, "cajero", "supervisor", "contador")
        self._app = app
        self._usuario = usuario

    def por_identificador(self, identificador: str) -> Factura:
        return self._app.facturas.obtener_factura(identificador)

    def de_cliente(self, cliente_id: str) -> list[Factura]:
        return self._app.facturas.por_cliente(cliente_id)

    def xml(self, identificador: str) -> str:
        """El XML timbrado. Una factura sin timbre no tiene XML valido que entregar."""
        factura = self.por_identificador(identificador)
        if factura.timbre is None:
            raise EstadoInvalido(f"La factura {identificador} no esta timbrada.")
        return generar_xml(factura, self._app.config)

    def pdf(self, identificador: str) -> bytes:
        return generar_pdf(self.por_identificador(identificador), self._app.config)

    def resumen_del_dia(self, dia: date) -> dict[str, object]:
        """Ventas e impuestos del dia. Solo para supervisor y contador."""
        exigir_rol(self._usuario, "supervisor", "contador")
        resumen = reportes.ventas_del_dia(self._app.facturas, dia)
        resumen["cierre"] = reportes.cierre_de_caja(self._app.facturas, dia)
        return resumen
