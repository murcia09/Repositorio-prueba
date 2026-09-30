import pytest

import facturacion.emision as emision
from facturacion.emision import VentaInvalida, emitir


class _FechaFija:
    @staticmethod
    def now(tz=None):
        class _Marca:
            def isoformat(self):
                return "2026-09-30T12:34:56+00:00"

        return _Marca()


def test_emitir_devuelve_factura_emitida_y_no_mutua_la_venta(monkeypatch):
    monkeypatch.setattr(emision, "datetime", _FechaFija)

    venta = {
        "id_venta": "V-1001",
        "total": 125.50,
        "moneda": "USD",
        "cliente": {"id_cliente": "C-42", "nombre": "Ana Pérez"},
        "lineas": [{"sku": "SKU-001", "cantidad": 1, "precio_unitario": 125.50}],
    }

    factura = emitir(venta)

    assert factura is not venta
    assert factura["emitida"] is True
    assert factura["estado"] == "emitida"
    assert factura["fecha_emision"] == "2026-09-30T12:34:56+00:00"
    assert factura["id_venta"] == "V-1001"
    assert venta.get("emitida") is None
    assert venta.get("estado") is None
    assert venta.get("fecha_emision") is None


def test_emitir_admite_total_cero_y_colecciones_vacias(monkeypatch):
    monkeypatch.setattr(emision, "datetime", _FechaFija)

    venta = {
        "id_venta": "V-1002",
        "total": 0,
        "cliente": None,
        "lineas": [],
    }

    factura = emitir(venta)

    assert factura["total"] == 0
    assert factura["cliente"] is None
    assert factura["lineas"] == []
    assert factura["emitida"] is True


@pytest.mark.parametrize(
    "venta, mensaje",
    [
        (None, "La venta debe ser un diccionario."),
        ({"total": 10}, "La venta debe incluir 'id_venta'."),
        ({"id_venta": "", "total": 10}, "La venta debe incluir 'id_venta'."),
        ({"id_venta": "V-1"}, "La venta debe incluir 'total'."),
        ({"id_venta": "V-1", "total": 10, "cliente": "no-es-dict"}, "'cliente' debe ser un diccionario cuando esté presente."),
        ({"id_venta": "V-1", "total": 10, "lineas": {}}, "'lineas' debe ser una lista cuando esté presente."),
    ],
)
def test_emitir_rechaza_ventas_invalidas(venta, mensaje):
    with pytest.raises(VentaInvalida, match=mensaje):
        emitir(venta)


def test_validar_venta_acepta_cliente_nulo_y_lineas_nulas():
    emision._validar_venta({"id_venta": "V-3", "total": 10, "cliente": None, "lineas": None})


def test_validar_venta_rechaza_total_presente_con_valor_none():
    with pytest.raises(VentaInvalida, match="La venta debe incluir 'total'."):
        emision._validar_venta({"id_venta": "V-4", "total": None})
