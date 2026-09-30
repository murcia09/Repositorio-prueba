import pytest

from facturacion.emision import emitir, sincronizar_pendientes


class VerificadorConectividadDisponible:
    def hay_conectividad(self):
        return True


class VerificadorConectividadSinRed:
    def hay_conectividad(self):
        return False


class ServicioTributarioOK:
    def __init__(self):
        self.enviadas = []

    def enviar(self, venta):
        self.enviadas.append(venta)
        return {"estado": "enviada", "id_venta": venta["id_venta"]}


class ServicioTributarioFalla:
    def __init__(self, excepcion):
        self.excepcion = excepcion
        self.enviadas = []

    def enviar(self, venta):
        self.enviadas.append(venta)
        raise self.excepcion


class ColaPendientesDoble:
    def __init__(self, pendientes=None):
        self.guardadas = []
        self._pendientes = list(pendientes or [])
        self.sincronizadas = []

    def guardar(self, venta):
        self.guardadas.append(venta)
        self._pendientes.append(venta)

    def pendientes(self):
        return list(self._pendientes)

    def marcar_sincronizada(self, venta):
        self.sincronizadas.append(venta)
        self._pendientes = [pendiente for pendiente in self._pendientes if pendiente != venta]


@pytest.fixture

def venta_valida():
    return {
        "id_venta": "V-1001",
        "total": 125.50,
        "moneda": "USD",
        "cliente": {"id_cliente": "C-42", "nombre": "Ana Pérez"},
        "lineas": [{"sku": "SKU-001", "cantidad": 1, "precio_unitario": 125.50}],
    }


def test_C1_emitir_deja_la_venta_en_cola_y_marca_contingencia_cuando_no_hay_conectividad(venta_valida):
    verificador = VerificadorConectividadSinRed()
    servicio = ServicioTributarioOK()
    cola = ColaPendientesDoble()

    resultado = emitir(
        venta_valida,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
        cola=cola,
    )

    assert resultado["estado"] in {"contingencia", "pendiente_sincronizacion", "pendiente"}
    assert cola.guardadas == [venta_valida]
    assert servicio.enviadas == []


def test_C1_emitir_deja_la_venta_en_cola_y_marca_contingencia_cuando_falla_el_servicio_tributario(venta_valida):
    verificador = VerificadorConectividadDisponible()
    servicio = ServicioTributarioFalla(RuntimeError("fallo tributario"))
    cola = ColaPendientesDoble()

    resultado = emitir(
        venta_valida,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
        cola=cola,
    )

    assert resultado["estado"] in {"contingencia", "pendiente_sincronizacion", "pendiente"}
    assert cola.guardadas == [venta_valida]
    assert servicio.enviadas == [venta_valida]


def test_C2_sincronizar_pendientes_envia_todas_las_facturas_pendientes_cuando_vuelve_la_red():
    pendientes = [
        {"id_venta": "V-2001", "total": 10},
        {"id_venta": "V-2002", "total": 20},
    ]
    cola = ColaPendientesDoble(pendientes=pendientes)
    verificador = VerificadorConectividadDisponible()
    servicio = ServicioTributarioOK()

    resultado = sincronizar_pendientes(
        cola=cola,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
    )

    assert servicio.enviadas == pendientes
    assert cola.sincronizadas == pendientes
    assert resultado["sincronizadas"] == 2
    assert resultado["pendientes"] == []


def test_C3_sincronizar_pendientes_no_reenvia_facturas_ya_sincronizadas_ni_duplica_registros():
    ya_sincronizada = {"id_venta": "V-3001", "total": 10, "estado_sync": "sincronizada"}
    pendiente = {"id_venta": "V-3002", "total": 20, "estado_sync": "pendiente"}
    cola = ColaPendientesDoble(pendientes=[ya_sincronizada, pendiente])
    verificador = VerificadorConectividadDisponible()
    servicio = ServicioTributarioOK()

    resultado = sincronizar_pendientes(
        cola=cola,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
    )

    assert servicio.enviadas == [pendiente]
    assert ya_sincronizada not in servicio.enviadas
    assert resultado["sincronizadas"] == 1
    assert resultado["pendientes"] == [ya_sincronizada]


def test_C4_emitir_devuelve_factura_emitida_cuando_hay_conectividad_y_el_servicio_tributario_responde_ok(venta_valida):
    verificador = VerificadorConectividadDisponible()
    servicio = ServicioTributarioOK()
    cola = ColaPendientesDoble()

    resultado = emitir(
        venta_valida,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
        cola=cola,
    )

    assert resultado["estado"] in {"emitida", "exitoso", "éxito"}
    assert resultado["id_venta"] == venta_valida["id_venta"]
    assert cola.guardadas == []
    assert servicio.enviadas == [venta_valida]
