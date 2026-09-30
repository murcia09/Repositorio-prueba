import pytest

from facturacion.emision import SincronizacionInvalida, emitir, sincronizar_pendientes


class VerificadorCallable:
    def __init__(self, disponible):
        self.disponible = disponible
        self.llamadas = 0

    def __call__(self):
        self.llamadas += 1
        return self.disponible


class ServicioCallable:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return self.respuesta


class ColaDoble:
    def __init__(self, pendientes=None):
        self.guardadas = []
        self._pendientes = list(pendientes or [])
        self.marcadas = []

    def guardar(self, venta):
        self.guardadas.append(venta)
        self._pendientes.append(venta)

    def pendientes(self):
        return list(self._pendientes)

    def marcar_sincronizada(self, venta):
        self.marcadas.append(venta)
        self._pendientes = [pendiente for pendiente in self._pendientes if pendiente != venta]


class ColaSinGuardar:
    def pendientes(self):
        return []


@pytest.fixture

def venta_base():
    return {"id_venta": "V-9001", "total": 50, "cliente": None, "lineas": []}


def test_emitir_con_service_callable_y_respuesta_no_dict_marca_emitida_y_respuesta(venta_base):
    verificador = VerificadorCallable(True)
    servicio = ServicioCallable("OK")
    cola = ColaDoble()

    factura = emitir(
        venta_base,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
        cola=cola,
    )

    assert verificador.llamadas == 1
    assert servicio.llamadas == [venta_base]
    assert cola.guardadas == []
    assert factura["estado"] == "emitida"
    assert factura["emitida"] is True
    assert factura["respuesta"] == "OK"
    assert factura["id_venta"] == "V-9001"


def test_emitir_cuando_no_hay_conectividad_guarda_copia_y_no_mutua_la_venta(venta_base):
    venta_original = dict(venta_base)
    verificador = VerificadorCallable(False)
    servicio = ServicioCallable({"estado": "emitida", "id_venta": venta_base["id_venta"]})
    cola = ColaDoble()

    factura = emitir(
        venta_original,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
        cola=cola,
    )

    assert factura["estado"] == "contingencia"
    assert factura["emitida"] is False
    assert factura["pendiente_sincronizacion"] is True
    assert cola.guardadas == [venta_base]
    assert cola.guardadas[0] is not venta_original
    assert servicio.llamadas == []


def test_sincronizar_pendientes_con_red_caida_no_reintenta_y_devuelve_pendientes_originales():
    pendientes = [{"id_venta": "V-1", "total": 10}, {"id_venta": "V-2", "total": 20}]
    cola = ColaDoble(pendientes=pendientes)
    verificador = VerificadorCallable(False)
    servicio = ServicioCallable({"estado": "emitida"})

    resultado = sincronizar_pendientes(
        cola=cola,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
    )

    assert resultado["sincronizadas"] == 0
    assert resultado["pendientes"] == pendientes
    assert servicio.llamadas == []
    assert cola.marcadas == []


def test_sincronizar_pendientes_omite_facturas_ya_sincronizadas_y_procesa_las_restantes():
    ya = {"id_venta": "V-10", "total": 1, "estado_sync": "sincronizada"}
    pendiente = {"id_venta": "V-11", "total": 2}
    cola = ColaDoble(pendientes=[ya, pendiente])
    verificador = VerificadorCallable(True)
    servicio = ServicioCallable({"estado": "emitida"})

    resultado = sincronizar_pendientes(
        cola=cola,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
    )

    assert resultado["sincronizadas"] == 1
    assert resultado["pendientes"] == [ya]
    assert servicio.llamadas == [pendiente]
    assert cola.marcadas == [pendiente]


def test_sincronizar_pendientes_deja_en_cola_las_ventas_que_fallan_al_enviar():
    pendiente_ok = {"id_venta": "V-20", "total": 1}
    pendiente_falla = {"id_venta": "V-21", "total": 2}
    cola = ColaDoble(pendientes=[pendiente_ok, pendiente_falla])
    verificador = VerificadorCallable(True)

    def servicio(venta):
        if venta["id_venta"] == "V-21":
            raise RuntimeError("servicio caído")
        return {"estado": "emitida", "id_venta": venta["id_venta"]}

    resultado = sincronizar_pendientes(
        cola=cola,
        verificador_conectividad=verificador,
        servicio_tributario=servicio,
    )

    assert resultado["sincronizadas"] == 1
    assert resultado["pendientes"] == [pendiente_falla]
    assert cola.marcadas == [pendiente_ok]


def test_sincronizar_pendientes_rechaza_cola_sin_metodo_guardar_en_emitir(venta_base):
    verificador = VerificadorCallable(False)

    with pytest.raises(SincronizacionInvalida, match="La cola no expone el método guardar\(...\)."):
        emitir(
            venta_base,
            verificador_conectividad=verificador,
            servicio_tributario=ServicioCallable({"estado": "emitida"}),
            cola=ColaSinGuardar(),
        )


def test_sincronizar_pendientes_rechaza_servicio_sin_interfaz_valida():
    cola = ColaDoble(pendientes=[{"id_venta": "V-30", "total": 5}])
    verificador = VerificadorCallable(True)

    with pytest.raises(SincronizacionInvalida, match="El servicio tributario no expone una interfaz válida."):
        sincronizar_pendientes(
            cola=cola,
            verificador_conectividad=verificador,
            servicio_tributario=object(),
        )
