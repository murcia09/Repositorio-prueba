from datetime import date
from decimal import Decimal

from facturacion.documentos.pdf import generar_pdf, lineas_de_texto, nombre_archivo_pdf
from facturacion.documentos.xml import generar_xml, nombre_archivo_xml
from facturacion.modelos import LineaFactura
from facturacion.servicios import reportes
from tests.conftest import CAFE, PAN


def _timbrada(app):
    cliente = app.clientes.obtener("c2")
    factura = app.emision.emitir(
        app.emision.crear_borrador(cliente, [LineaFactura(CAFE, 1), LineaFactura(PAN, 2)])
    )
    return app.timbrado.timbrar(factura)


def test_el_xml_lleva_emisor_receptor_impuestos_y_timbre(app):
    factura = _timbrada(app)
    xml = generar_xml(factura, app.config)
    assert 'Folio="1"' in xml and 'Nit="900123456-8"' in xml
    assert 'Tasa="0.19"' in xml and factura.timbre.uuid in xml
    assert nombre_archivo_xml(factura) == "FV-1.xml"


def test_el_pdf_es_un_pdf_con_el_total(app):
    factura = _timbrada(app)
    pdf = generar_pdf(factura, app.config)
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
    assert any("Total:" in linea for linea in lineas_de_texto(factura, app.config))
    assert nombre_archivo_pdf(factura) == "FV-1.pdf"


def test_reportes_del_dia(app):
    factura = _timbrada(app)
    hoy = factura.fecha_emision.date()
    resumen = reportes.ventas_del_dia(app.facturas, hoy)
    assert resumen["facturas"] == 1 and resumen["total"] == factura.total
    assert reportes.productos_mas_vendidos(app.facturas) == [("PAN-001", 2), ("CAF-250", 1)]
    assert reportes.impuestos_por_tasa(app.facturas, hoy, hoy)[Decimal("0.19")] == Decimal("2375.00")


def test_las_anuladas_no_cuentan_como_venta(app):
    factura = _timbrada(app)
    app.anulacion.anular(factura.identificador, "Prueba")
    assert reportes.ventas_del_dia(app.facturas, factura.fecha_emision.date())["facturas"] == 0
    assert reportes.ventas_del_dia(app.facturas, date(2000, 1, 1))["facturas"] == 0
