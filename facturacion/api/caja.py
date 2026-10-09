"""Punto de venta: lo que usa el cajero para vender, facturar y cobrar.

`facturar()` es el boton "Facturar" de la caja: emite y timbra la factura del
carrito, y registra cuanto tardo, que es lo que el negocio mide en la atencion al
cliente.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from facturacion.aplicacion import Aplicacion
from facturacion.errores import FacturaInvalida
from facturacion.modelos import Factura, LineaFactura, MedioPago
from facturacion.seguridad.autenticacion import Usuario, exigir_rol
from facturacion.servicios.calculos import calcular_totales
from facturacion.utilidades.cronometro import Cronometro
from facturacion.utilidades.validaciones import validar_cantidad


@dataclass
class ResultadoFacturacion:
    factura: Factura
    milisegundos: float


class PuntoDeVenta:
    def __init__(self, app: Aplicacion, usuario: Usuario) -> None:
        exigir_rol(usuario, "cajero", "supervisor")
        self._app = app
        self._usuario = usuario
        self._carrito: list[LineaFactura] = []

    @property
    def carrito(self) -> list[LineaFactura]:
        return list(self._carrito)

    def agregar(self, codigo: str, cantidad: int = 1) -> None:
        """Suma un producto al carrito; si ya estaba, acumula la cantidad."""
        if not validar_cantidad(cantidad):
            raise FacturaInvalida(f"Cantidad no valida: {cantidad}.")
        producto = self._app.inventario.producto(codigo)
        for i, linea in enumerate(self._carrito):
            if linea.producto.codigo == codigo:
                self._carrito[i] = LineaFactura(producto, linea.cantidad + cantidad, linea.descuento)
                return
        self._carrito.append(LineaFactura(producto, cantidad))

    def quitar(self, codigo: str) -> None:
        self._carrito = [linea for linea in self._carrito if linea.producto.codigo != codigo]

    def vaciar(self) -> None:
        self._carrito = []

    def total_carrito(self) -> Decimal:
        """El total con impuestos que se muestra al cliente antes de facturar."""
        if not self._carrito:
            return Decimal("0")
        cliente = self._app.clientes.consumidor_final()
        return calcular_totales(Factura("", cliente, list(self._carrito))).total

    def facturar(self, cliente_id: str | None = None) -> ResultadoFacturacion:
        """Emite y timbra la factura del carrito. Sin cliente, a consumidor final."""
        if not self._carrito:
            raise FacturaInvalida("El carrito esta vacio: no hay nada que facturar.")
        cliente = (
            self._app.clientes.obtener(cliente_id)
            if cliente_id
            else self._app.clientes.consumidor_final()
        )
        with Cronometro() as reloj:
            borrador = self._app.emision.crear_borrador(cliente, self._carrito)
            factura = self._app.emision.emitir(borrador)
            factura = self._app.timbrado.timbrar(factura)
        self._app.auditoria.registrar(
            "tiempo_facturacion",
            factura=factura.identificador,
            milisegundos=round(reloj.milisegundos, 1),
            cajero=self._usuario.id,
        )
        self.vaciar()
        return ResultadoFacturacion(factura, reloj.milisegundos)

    def cobrar(
        self, identificador: str, medio: MedioPago, monto: object, referencia: str | None = None
    ) -> Decimal:
        """Registra el pago y devuelve el cambio que hay que entregar al cliente."""
        _, cambio = self._app.pagos.registrar_pago(identificador, medio, monto, referencia)
        return cambio
