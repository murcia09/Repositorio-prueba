from types import SimpleNamespace

import pytest

from facturacion import emitir
import facturacion.emision as emision


class _FakeUUID:
    def __init__(self, hex_value: str):
        self.hex = hex_value


class _FakeDateTime:
    @staticmethod
    def now(tz=None):
        return SimpleNamespace(isoformat=lambda: "2026-10-01T12:34:56+00:00")


def test_emitir_con_venta_valida_devuelve_factura_emitida(monkeypatch):
    monkeypatch.setattr(emision, "uuid4", lambda: _FakeUUID("abcdef1234567890"))
    monkeypatch.setattr(emision, "datetime", _FakeDateTime)

    venta = {
        "id": "V-1001",
        "total": 125.5,
        "moneda": "USD",
        "items": [
            {"sku": "SKU-001", "cantidad": 1, "precio_unitario": 125.5},
        ],
    }

    resultado = emitir(venta)

    assert resultado == {
        "estado": "emitida",
        "emitida": True,
        "factura_emitida": True,
        "factura_id": "F-ABCDEF123456",
        "venta_id": "V-1001",
        "total": 125.5,
        "moneda": "USD",
        "emitida_en": "2026-10-01T12:34:56+00:00",
    }


def test_emitir_asigna_moneda_usd_por_defecto(monkeypatch):
    monkeypatch.setattr(emision, "uuid4", lambda: _FakeUUID("0011223344556677"))
    monkeypatch.setattr(emision, "datetime", _FakeDateTime)

    venta = {
        "id": "V-1002",
        "total": 10,
        "items": [
            {"sku": "SKU-002", "cantidad": 2, "precio_unitario": 5},
        ],
    }

    resultado = emitir(venta)

    assert resultado["moneda"] == "USD"
    assert resultado["venta_id"] == "V-1002"


@pytest.mark.parametrize(
    "venta, mensaje",
    [
        (None, "diccionario"),
        ([], "diccionario"),
        ({"total": 10, "items": [{"sku": "SKU-1", "cantidad": 1, "precio_unitario": 10}]}, "identificador"),
        ({"id": "V-1", "total": 0, "items": [{"sku": "SKU-1", "cantidad": 1, "precio_unitario": 10}]}, "mayor que cero"),
        ({"id": "V-1", "total": 10, "items": []}, "al menos un ítem"),
        ({"id": "V-1", "total": 10, "items": ["no-dict"]}, "diccionario"),
        ({"id": "V-1", "total": 10, "items": [{"cantidad": 1, "precio_unitario": 10}]}, "SKU"),
        ({"id": "V-1", "total": 10, "items": [{"sku": "SKU-1", "cantidad": 0, "precio_unitario": 10}]}, "entero mayor que cero"),
        ({"id": "V-1", "total": 10, "items": [{"sku": "SKU-1", "cantidad": 1, "precio_unitario": 0}]}, "numérico y mayor que cero"),
    ],
)

def test_emitir_rechaza_ventas_invalidas_con_valueerror(venta, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        emitir(venta)


def test_emitir_rechaza_total_no_numerico():
    venta = {
        "id": "V-1003",
        "total": "10",
        "items": [{"sku": "SKU-003", "cantidad": 1, "precio_unitario": 10}],
    }

    with pytest.raises(ValueError, match="total numérico"):
        emitir(venta)


def test_emitir_rechaza_cantidad_no_entera():
    venta = {
        "id": "V-1004",
        "total": 10,
        "items": [{"sku": "SKU-004", "cantidad": 1.5, "precio_unitario": 10}],
    }

    with pytest.raises(ValueError, match="entero mayor que cero"):
        emitir(venta)
