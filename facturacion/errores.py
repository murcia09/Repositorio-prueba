"""Errores del dominio de facturacion.

Todos heredan de ErrorFacturacion para que la caja pueda mostrar un mensaje al
cajero sin conocer cada caso. El mensaje siempre dice que paso y, si se puede, que
hacer.
"""

from __future__ import annotations


class ErrorFacturacion(Exception):
    """Error de negocio con un mensaje que se puede mostrar al usuario."""


class ClienteInvalido(ErrorFacturacion):
    """Datos del cliente incompletos o con formato incorrecto."""


class ProductoNoEncontrado(ErrorFacturacion):
    """El codigo no corresponde a ningun producto del catalogo."""


class StockInsuficiente(ErrorFacturacion):
    """No hay existencias para cubrir lo que se quiere vender."""

    def __init__(self, codigo: str, solicitado: int, disponible: int) -> None:
        super().__init__(
            f"No hay existencias suficientes de {codigo}: se pidieron {solicitado} "
            f"y hay {disponible}."
        )
        self.codigo = codigo
        self.solicitado = solicitado
        self.disponible = disponible


class FacturaInvalida(ErrorFacturacion):
    """La factura no cumple una regla de negocio: sin lineas, descuento excesivo..."""


class FacturaNoEncontrada(ErrorFacturacion):
    """No existe una factura con ese identificador."""


class EstadoInvalido(ErrorFacturacion):
    """La factura no esta en el estado que la operacion necesita."""


class ServicioImpuestosNoDisponible(ErrorFacturacion):
    """El servicio de impuestos no respondio o rechazo la conexion."""


class ErrorTimbrado(ErrorFacturacion):
    """No se pudo timbrar la factura despues de los reintentos."""


class PagoRechazado(ErrorFacturacion):
    """El pago no se puede aplicar: monto, medio o referencia incorrectos."""


class ErrorCorreo(ErrorFacturacion):
    """No se pudo enviar un correo al cliente."""


class PermisoDenegado(ErrorFacturacion):
    """El usuario no tiene el rol que la operacion exige."""


class TokenInvalido(ErrorFacturacion):
    """La cabecera de autenticacion falta, esta mal formada o el token expiro."""
