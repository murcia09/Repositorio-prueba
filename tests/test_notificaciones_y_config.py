from decimal import Decimal

import pytest

from facturacion.config import Configuracion
from facturacion.errores import ErrorCorreo
from facturacion.modelos import LineaFactura
from tests.conftest import CAFE


def test_aviso_de_anulacion_al_cliente_con_correo(app, correo):
    cliente = app.clientes.obtener("c1")
    factura = app.timbrado.timbrar(
        app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(CAFE, 1)]))
    )
    app.anulacion.anular(factura.identificador, "Cliente desistio")
    assert app.notificaciones.avisar_anulacion(factura) is True
    assert correo.enviados[0].destinatario == "ana@example.com"
    assert "Cliente desistio" in correo.enviados[0].cuerpo


def test_sin_correo_no_se_avisa(app, correo):
    cliente = app.clientes.obtener("c2")
    factura = app.timbrado.timbrar(
        app.emision.emitir(app.emision.crear_borrador(cliente, [LineaFactura(CAFE, 1)]))
    )
    assert app.notificaciones.avisar_anulacion(factura) is False
    assert correo.enviados == []


def test_un_destinatario_invalido_se_rechaza(app):
    with pytest.raises(ErrorCorreo):
        app.notificaciones.enviar("no-es-correo", "Asunto", "Cuerpo")


def test_la_configuracion_se_lee_del_entorno():
    config = Configuracion.desde_entorno(
        {"FACTURACION_SERIE": "FE", "FACTURACION_IVA": "0.05", "FACTURACION_TIMEOUT_TIMBRADO_S": "0.8"}
    )
    assert config.serie_facturas == "FE"
    assert config.tasa_iva_general == Decimal("0.05")
    assert config.timeout_timbrado_s == 0.8
    assert config.reintentos_timbrado == 2, "Lo que no viene en el entorno queda por defecto"
