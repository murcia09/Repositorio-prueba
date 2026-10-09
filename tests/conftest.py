"""Una aplicacion lista para vender: catalogo, existencias, clientes y un cajero."""

from __future__ import annotations

from decimal import Decimal

import pytest

from facturacion.aplicacion import construir_aplicacion
from facturacion.integraciones.correo import CorreoEnMemoria
from facturacion.integraciones.servicio_impuestos import ServicioImpuestosSimulado
from facturacion.modelos import Cliente, Producto
from facturacion.seguridad.autenticacion import Usuario

CAFE = Producto("CAF-250", "Cafe molido 250 g", Decimal("12500"))
PAN = Producto("PAN-001", "Pan tajado", Decimal("6800"), tasa_iva=Decimal("0"))
ENVIO = Producto("SRV-ENV", "Envio a domicilio", Decimal("5000"), controla_inventario=False)


@pytest.fixture
def impuestos() -> ServicioImpuestosSimulado:
    return ServicioImpuestosSimulado()


@pytest.fixture
def correo() -> CorreoEnMemoria:
    return CorreoEnMemoria()


@pytest.fixture
def app(impuestos, correo):
    app = construir_aplicacion(servicio_impuestos=impuestos, correo=correo)
    app.inventario.registrar_producto(CAFE, existencias=50)
    app.inventario.registrar_producto(PAN, existencias=30)
    app.inventario.registrar_producto(ENVIO)
    app.clientes.registrar(Cliente("c1", "Ana Gomez", "1032456789", correo="ana@example.com"))
    app.clientes.registrar(Cliente("c2", "Comercial Andina", "900123456-8"))
    return app


@pytest.fixture
def cajero() -> Usuario:
    return Usuario("u1", "Carlos", frozenset({"cajero"}))


@pytest.fixture
def supervisor() -> Usuario:
    return Usuario("u2", "Marta", frozenset({"supervisor"}))
