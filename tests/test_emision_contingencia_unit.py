import pytest

import facturacion.emision as emision


class FakeUUID:
    def __init__(self, hex_value):
        self.hex = hex_value


class FakeDateTime:
    @staticmethod
    def now(tz=None):
        class _Moment:
            @staticmethod
            def isoformat():
                return "2026-10-01T12:00:00+00:00"

        return _Moment()


class ColaConAppend:
    def __init__(self):
        self.items = []

    def append(self, item):
        self.items.append(item)


class VerificadorCallableFalso:
    def __call__(self):
        return False


class ProcesadorCallableQueDevuelveDict:
    def __call__(self, venta):
        return {
            "estado": "emitida",
            "serie": "A",
            "numero_autorizacion": "AUTH-001",
            "venta_id": venta["id"],
        }


class ProcesadorCallableQueFalla:
    def __call__(self, venta):
        raise RuntimeError("servicio tributario caido")


class SincronizadorQueFallaEnLaSegunda(self := object):
    pass


class SincronizadorCallableQueFallaEnUnaFactura:
    def __init__(self, fallo_en_factura_id):
        self.fallo_en_factura_id = fallo_en_factura_id
        self.llamadas = []

    def __call__(self, factura):
        self.llamadas.append(factura["factura_id"])
        if factura["factura_id"] == self.fallo_en_factura_id:
            raise RuntimeError("no sincronizada")
        return True


class ColaConPendientes:
    def __init__(self, pendientes):
        self.pendientes = pendientes


@pytest.fixture
def venta_valida():
    return {
        "id": "V-9001",
        "total": 100,
        "items": [{"sku": "SKU-9001", "cantidad": 2, "precio_unitario": 50}],
    }


def test_emitir_registra_en_cola_con_append_cuando_hay_contingencia_por_conexion(monkeypatch, venta_valida):
    monkeypatch.setattr(emision, "uuid4", lambda: FakeUUID("abcdef1234567890"))
    monkeypatch.setattr(emision, "datetime", FakeDateTime)

    cola = ColaConAppend()

    resultado = emision.emitir(
        venta_valida,
        verificador_conexion=VerificadorCallableFalso(),
        procesador_tributario=ProcesadorCallableQueDevuelveDict(),
        cola_pendientes=cola,
    )

    assert resultado["estado"] == "contingencia"
    assert resultado["pendiente_sincronizacion"] is True
    assert cola.items[0]["venta_id"] == "V-9001"
    assert cola.items[0]["factura_id"] == "F-ABCDEF123456"


def test_emitir_combina_el_resultado_tributario_cuando_devuelve_un_diccionario(monkeypatch, venta_valida):
    monkeypatch.setattr(emision, "uuid4", lambda: FakeUUID("0011223344556677"))
    monkeypatch.setattr(emision, "datetime", FakeDateTime)

    resultado = emision.emitir(
        venta_valida,
        verificador_conexion=lambda: True,
        procesador_tributario=ProcesadorCallableQueDevuelveDict(),
        cola_pendientes=None,
    )

    assert resultado["estado"] == "emitida"
    assert resultado["serie"] == "A"
    assert resultado["numero_autorizacion"] == "AUTH-001"
    assert resultado["venta_id"] == "V-9001"


def test_emitir_registra_en_cola_y_devuelve_contingencia_si_falla_el_procesador_tributario(monkeypatch, venta_valida):
    monkeypatch.setattr(emision, "uuid4", lambda: FakeUUID("fedcba9876543210"))
    monkeypatch.setattr(emision, "datetime", FakeDateTime)

    cola = ColaConAppend()

    resultado = emision.emitir(
        venta_valida,
        verificador_conexion=lambda: True,
        procesador_tributario=ProcesadorCallableQueFalla(),
        cola_pendientes=cola,
    )

    assert resultado["estado"] == "contingencia"
    assert resultado["pendiente_sincronizacion"] is True
    assert len(cola.items) == 1
    assert cola.items[0]["venta_id"] == "V-9001"


def test_emitir_rechaza_verificador_conexion_invalido(venta_valida):
    with pytest.raises(TypeError, match="verificador_conexion"):
        emision.emitir(
            venta_valida,
            verificador_conexion=object(),
            procesador_tributario=None,
            cola_pendientes=None,
        )


def test_emitir_rechaza_procesador_tributario_invalido(venta_valida):
    with pytest.raises(TypeError, match="procesador_tributario"):
        emision.emitir(
            venta_valida,
            verificador_conexion=lambda: True,
            procesador_tributario=object(),
            cola_pendientes=None,
        )


def test_emitir_rechaza_cola_sin_append_ni_registrar(venta_valida):
    class ColaInvalida:
        pass

    with pytest.raises(TypeError, match="cola de pendientes"):
        emision.emitir(
            venta_valida,
            verificador_conexion=lambda: False,
            procesador_tributario=None,
            cola_pendientes=ColaInvalida(),
        )


def test_sincronizar_pendientes_reporta_errores_sin_detener_el_resto():
    pendientes = [
        {"factura_id": "F-1", "venta_id": "V-1"},
        {"factura_id": "F-2", "venta_id": "V-2"},
        {"factura_id": "F-3", "venta_id": "V-3"},
    ]
    sincronizador = SincronizadorCallableQueFallaEnUnaFactura("F-2")

    resultado = emision.sincronizar_pendientes(ColaConPendientes(pendientes), sincronizador=sincronizador)

    assert resultado["pendientes_total"] == 3
    assert resultado["sincronizadas"] == 2
    assert resultado["errores"] == [{"factura_id": "F-2", "error": "no sincronizada"}]
    assert sincronizador.llamadas == ["F-1", "F-2", "F-3"]


def test_sincronizar_pendientes_rechaza_sincronizador_invalido():
    with pytest.raises(TypeError, match="sincronizador"):
        emision.sincronizar_pendientes([{"factura_id": "F-1"}], sincronizador=object())


def test_sincronizar_pendientes_con_cola_nula_devuelve_ceros():
    resultado = emision.sincronizar_pendientes(None, sincronizador=lambda factura: True)

    assert resultado == {"sincronizadas": 0, "pendientes_total": 0, "errores": []}
