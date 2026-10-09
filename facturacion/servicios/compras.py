"""Compras a proveedores: ordenes de compra y recepcion de mercancia.

Recibir una orden suma las unidades al inventario. Se puede recibir por partes; la
orden queda cerrada cuando llego todo lo pedido.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from facturacion.errores import EstadoInvalido, FacturaInvalida
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.inventario import ServicioInventario
from facturacion.utilidades.dinero import redondear, sumar
from facturacion.utilidades.fechas import ahora
from facturacion.utilidades.validaciones import validar_cantidad, validar_nit


@dataclass
class Proveedor:
    nit: str
    nombre: str
    dias_credito: int = 30


@dataclass
class LineaCompra:
    codigo: str
    cantidad: int
    costo_unitario: Decimal
    recibida: int = 0

    @property
    def pendiente(self) -> int:
        return self.cantidad - self.recibida


@dataclass
class OrdenCompra:
    numero: int
    proveedor: Proveedor
    lineas: list[LineaCompra]
    fecha: datetime
    cerrada: bool = False
    recepciones: list[datetime] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sumar(redondear(l.costo_unitario * l.cantidad) for l in self.lineas)


class ServicioCompras:
    def __init__(self, inventario: ServicioInventario, auditoria: RegistroAuditoria) -> None:
        self._inventario = inventario
        self._auditoria = auditoria
        self._ordenes: dict[int, OrdenCompra] = {}
        self._siguiente = 1

    def crear_orden(self, proveedor: Proveedor, lineas: list[LineaCompra]) -> OrdenCompra:
        if not validar_nit(proveedor.nit):
            raise FacturaInvalida(f"El NIT del proveedor {proveedor.nit} no es valido.")
        if not lineas:
            raise FacturaInvalida("Una orden de compra necesita al menos una linea.")
        for linea in lineas:
            self._inventario.producto(linea.codigo)
            if not validar_cantidad(linea.cantidad) or linea.costo_unitario <= 0:
                raise FacturaInvalida(f"Linea de compra no valida para {linea.codigo}.")
        orden = OrdenCompra(self._siguiente, proveedor, list(lineas), ahora())
        self._ordenes[orden.numero] = orden
        self._siguiente += 1
        self._auditoria.registrar("orden_compra_creada", numero=orden.numero, total=str(orden.total))
        return orden

    def recibir(self, numero: int, recibido: dict[str, int]) -> OrdenCompra:
        """Registra lo que llego del proveedor y lo suma al inventario."""
        orden = self._ordenes.get(numero)
        if orden is None:
            raise FacturaInvalida(f"No existe la orden de compra {numero}.")
        if orden.cerrada:
            raise EstadoInvalido(f"La orden {numero} ya se recibio completa.")
        por_codigo = {l.codigo: l for l in orden.lineas}
        for codigo, cantidad in recibido.items():
            linea = por_codigo.get(codigo)
            if linea is None or not 0 < cantidad <= linea.pendiente:
                raise FacturaInvalida(f"No se puede recibir {cantidad} de {codigo} en la orden {numero}.")
        for codigo, cantidad in recibido.items():
            por_codigo[codigo].recibida += cantidad
            self._inventario.agregar_existencias(codigo, cantidad)
        orden.recepciones.append(ahora())
        orden.cerrada = all(l.pendiente == 0 for l in orden.lineas)
        self._auditoria.registrar("mercancia_recibida", orden=numero, cerrada=orden.cerrada)
        return orden

    def pendientes(self) -> list[OrdenCompra]:
        return [o for o in self._ordenes.values() if not o.cerrada]
