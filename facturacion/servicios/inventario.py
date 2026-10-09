"""Existencias de productos. Se descuentan al emitir y se devuelven al anular."""

from __future__ import annotations

from facturacion.errores import ProductoNoEncontrado, StockInsuficiente
from facturacion.modelos import LineaFactura, Producto
from facturacion.repositorios.memoria import RepositorioProductos


class ServicioInventario:
    def __init__(self, productos: RepositorioProductos) -> None:
        self._productos = productos
        self._existencias: dict[str, int] = {}

    def registrar_producto(self, producto: Producto, existencias: int = 0) -> None:
        self._productos.guardar_producto(producto)
        self._existencias[producto.codigo] = existencias

    def producto(self, codigo: str) -> Producto:
        producto = self._productos.obtener(codigo)
        if producto is None:
            raise ProductoNoEncontrado(f"No existe el producto {codigo}.")
        return producto

    def disponibles(self, codigo: str) -> int:
        self.producto(codigo)
        return self._existencias.get(codigo, 0)

    def agregar_existencias(self, codigo: str, cantidad: int) -> int:
        self.producto(codigo)
        self._existencias[codigo] = self._existencias.get(codigo, 0) + cantidad
        return self._existencias[codigo]

    def reservar(self, lineas: list[LineaFactura]) -> None:
        """Descuenta las existencias de todas las lineas, o de ninguna.

        Primero se comprueba todo y despues se descuenta: si la tercera linea no tiene
        existencias, las dos primeras no deben quedar descontadas.
        """
        necesarias: dict[str, int] = {}
        for linea in lineas:
            if linea.producto.controla_inventario:
                codigo = linea.producto.codigo
                necesarias[codigo] = necesarias.get(codigo, 0) + linea.cantidad
        for codigo, cantidad in necesarias.items():
            disponible = self.disponibles(codigo)
            if cantidad > disponible:
                raise StockInsuficiente(codigo, cantidad, disponible)
        for codigo, cantidad in necesarias.items():
            self._existencias[codigo] -= cantidad

    def liberar(self, lineas: list[LineaFactura]) -> None:
        """Devuelve al inventario lo que se habia reservado, por ejemplo al anular."""
        for linea in lineas:
            if linea.producto.controla_inventario:
                self.agregar_existencias(linea.producto.codigo, linea.cantidad)
