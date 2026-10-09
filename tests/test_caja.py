from datetime import date
from decimal import Decimal

import pytest

from facturacion.api.caja import PuntoDeVenta
from facturacion.api.consultas import ConsultaFacturas
from facturacion.errores import FacturaInvalida, PermisoDenegado
from facturacion.modelos import EstadoFactura, MedioPago
from facturacion.seguridad.autenticacion import Usuario


def test_facturar_emite_timbra_y_registra_el_tiempo(app, cajero):
    caja = PuntoDeVenta(app, cajero)
    caja.agregar("CAF-250", 2)
    caja.agregar("PAN-001")
    resultado = caja.facturar("c1")
    assert resultado.factura.estado == EstadoFactura.TIMBRADA
    assert resultado.milisegundos >= 0
    assert app.auditoria.ultimo("tiempo_facturacion").datos["cajero"] == "u1"
    assert caja.carrito == [], "Despues de facturar el carrito queda vacio"


def test_sin_cliente_se_factura_a_consumidor_final(app, cajero):
    caja = PuntoDeVenta(app, cajero)
    caja.agregar("PAN-001")
    assert caja.facturar().factura.cliente.nombre == "Consumidor final"


def test_agregar_dos_veces_acumula(app, cajero):
    caja = PuntoDeVenta(app, cajero)
    caja.agregar("CAF-250")
    caja.agregar("CAF-250", 2)
    assert [(l.producto.codigo, l.cantidad) for l in caja.carrito] == [("CAF-250", 3)]
    assert caja.total_carrito() == Decimal("44625.00")


def test_carrito_vacio_no_se_factura(app, cajero):
    with pytest.raises(FacturaInvalida):
        PuntoDeVenta(app, cajero).facturar()


def test_cobrar_desde_la_caja(app, cajero):
    caja = PuntoDeVenta(app, cajero)
    caja.agregar("PAN-001")
    factura = caja.facturar().factura
    assert caja.cobrar(factura.identificador, MedioPago.EFECTIVO, 10000) == Decimal("3200.00")


def test_un_contador_no_puede_usar_la_caja(app):
    with pytest.raises(PermisoDenegado):
        PuntoDeVenta(app, Usuario("u3", "Luis", frozenset({"contador"})))


def test_consultas_y_resumen_del_dia(app, cajero, supervisor):
    caja = PuntoDeVenta(app, cajero)
    caja.agregar("CAF-250")
    factura = caja.facturar("c1").factura
    caja.cobrar(factura.identificador, MedioPago.EFECTIVO, factura.total)

    consultas = ConsultaFacturas(app, supervisor)
    assert factura.timbre.uuid in consultas.xml(factura.identificador)
    assert consultas.pdf(factura.identificador).startswith(b"%PDF")
    resumen = consultas.resumen_del_dia(date.today())
    assert resumen["facturas"] == 1 and resumen["cierre"] == {"efectivo": factura.total}

    with pytest.raises(PermisoDenegado):
        ConsultaFacturas(app, cajero).resumen_del_dia(date.today())
