"""Promociones, devoluciones, turnos, compras, puntos, contabilidad y catalogo."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from facturacion.errores import EstadoInvalido, FacturaInvalida, PagoRechazado
from facturacion.integraciones.catalogo_csv import cargar_catalogo
from facturacion.integraciones.exportacion_contable import CUENTA_CAJA, CUENTA_IVA, asientos, exportar_csv
from facturacion.modelos import LineaFactura, MedioPago
from facturacion.servicios.compras import LineaCompra, Proveedor, ServicioCompras
from facturacion.servicios.devoluciones import ItemDevuelto, ServicioDevoluciones
from facturacion.servicios.fidelizacion import ProgramaPuntos
from facturacion.servicios.promociones import Cupon, MotorPromociones, PromocionLleveNPagueM, PromocionPorcentaje
from facturacion.servicios.turnos_caja import ServicioTurnos
from tests.conftest import CAFE, PAN

HOY = date.today()


def _pagada(app, lineas, cliente="c1"):
    factura = app.emision.emitir(app.emision.crear_borrador(app.clientes.obtener(cliente), lineas))
    app.timbrado.timbrar(factura)
    app.pagos.registrar_pago(factura.identificador, MedioPago.EFECTIVO, factura.total)
    return factura


def test_se_aplica_la_promocion_mas_favorable():
    motor = MotorPromociones()
    motor.agregar_porcentaje(PromocionPorcentaje("Cafe 10", frozenset({"CAF-250"}), Decimal("0.10"), HOY, HOY))
    motor.agregar_lleve_pague(PromocionLleveNPagueM("3x2 cafe", "CAF-250", 3, 2))
    [linea] = motor.aplicar([LineaFactura(CAFE, 3)], HOY)
    assert linea.descuento == Decimal("12500.00"), "Una unidad gratis gana al 10 %"


def test_la_promocion_vencida_no_aplica():
    motor = MotorPromociones()
    ayer = HOY - timedelta(days=1)
    motor.agregar_porcentaje(PromocionPorcentaje("Vencida", frozenset({"PAN-001"}), Decimal("0.5"), ayer, ayer))
    assert motor.aplicar([LineaFactura(PAN, 1)], HOY)[0].descuento == 0


def test_un_cupon_se_usa_una_vez():
    motor = MotorPromociones()
    motor.agregar_cupon(Cupon("BIENVENIDA", Decimal("3000")))
    lineas = motor.redimir_cupon("bienvenida", [LineaFactura(CAFE, 1), LineaFactura(PAN, 1)])
    assert sum(l.descuento for l in lineas) == Decimal("3000")
    with pytest.raises(FacturaInvalida):
        motor.redimir_cupon("BIENVENIDA", lineas)


def test_devolucion_parcial_genera_nota_y_reingresa(app):
    factura = _pagada(app, [LineaFactura(CAFE, 4)])
    devoluciones = ServicioDevoluciones(app.facturas, app.inventario, app.notas_credito, app.auditoria)
    nota = devoluciones.devolver(factura.identificador, [ItemDevuelto("CAF-250", 1)], "Empaque roto")
    assert nota.monto == Decimal("14875.00")
    assert app.inventario.disponibles("CAF-250") == 47
    with pytest.raises(FacturaInvalida):
        devoluciones.devolver(factura.identificador, [ItemDevuelto("CAF-250", 4)], "Otra vez")


def test_arqueo_de_caja(app):
    turnos = ServicioTurnos(app.facturas, app.auditoria)
    turnos.abrir("u1", 100000)
    _pagada(app, [LineaFactura(PAN, 1)])
    turnos.registrar_movimiento("u1", "retiro", 20000, "Consignacion")
    turno = turnos.cerrar("u1", 86800)
    assert turno.diferencia == Decimal("0.00")
    with pytest.raises(EstadoInvalido):
        turnos.registrar_movimiento("u1", "ingreso", 1000, "Tarde")


def test_recepcion_parcial_de_una_compra(app):
    compras = ServicioCompras(app.inventario, app.auditoria)
    orden = compras.crear_orden(Proveedor("900123456-8", "Distribuidora"), [LineaCompra("PAN-001", 10, Decimal("4000"))])
    compras.recibir(orden.numero, {"PAN-001": 4})
    assert app.inventario.disponibles("PAN-001") == 34 and not orden.cerrada
    compras.recibir(orden.numero, {"PAN-001": 6})
    assert orden.cerrada and compras.pendientes() == []


def test_puntos_sobre_lo_pagado(app):
    puntos = ProgramaPuntos(app.auditoria)
    factura = _pagada(app, [LineaFactura(CAFE, 2)])
    assert puntos.acumular(factura) == 29
    assert puntos.acumular(factura) == 0, "Una factura acumula una sola vez"
    assert puntos.redimir("c1", 10) == Decimal("100.00")
    with pytest.raises(PagoRechazado):
        puntos.redimir("c1", 100)


def test_asientos_contables_cuadran(app):
    factura = _pagada(app, [LineaFactura(CAFE, 1), LineaFactura(PAN, 1)])
    filas = asientos(factura)
    debitos = sum(Decimal(f["debito"]) for f in filas)
    creditos = sum(Decimal(f["credito"]) for f in filas)
    assert debitos == creditos
    assert {f["cuenta"] for f in filas} >= {CUENTA_CAJA, CUENTA_IVA}
    assert factura.identificador in exportar_csv(app.facturas, HOY, HOY)


def test_carga_de_catalogo_con_errores_por_linea(app):
    texto = "codigo,descripcion,precio,iva,existencias\nLEC-1,Leche,4200,0,12\nMAL-1,Sin precio,abc,0,1\n"
    resultado = cargar_catalogo(texto, app.inventario)
    assert resultado.cargados == 1
    assert resultado.errores and resultado.errores[0].startswith("Linea 3")
    assert app.inventario.disponibles("LEC-1") == 12
