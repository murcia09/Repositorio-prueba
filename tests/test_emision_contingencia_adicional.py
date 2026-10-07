from types import SimpleNamespace

import pytest

from facturacion.emision import emitir, sincronizar_pendientes


class ColaContingenciaConPendientes:
    def __init__(self, pendientes=None):
        self.pendientes = list(pendientes or [])
        self.guardados = []

    def guardar(self, elemento):
        self.guardados.append(elemento)
        self.pendientes.append(elemento)


class ColaContingenciaSinGuardar:
    pass


class ClienteTributarioExitoso:
    def __init__(self):
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        return {"ok": True}


class DetectorConexionConRed:
    def __init__(self):
        self.llamadas = 0

    def __call__(self):
        self.llamadas += 1
        return True


class SincronizadorQueFallaEnLaSegunda:
    def __init__(self):
        self.llamadas = []

    def __call__(self, factura_pendiente):
        self.llamadas.append(factura_pendiente)
        return len(self.llamadas) == 1


def test_emitir_con_red_y_servicio_tributario_ok_devuelve_factura_emitida_y_no_usa_cola():
    venta = SimpleNamespace(identificador="VENTA-301")
    detector_conexion = DetectorConexionConRed()
    cliente_tributario = ClienteTributarioExitoso()
    cola_contingencia = ColaContingenciaConPendientes()

    factura = emitir(
        venta,
        detector_conexion=detector_conexion,
        cliente_tributario=cliente_tributario,
        cola_contingencia=cola_contingencia,
    )

    assert detector_conexion.llamadas == 1
    assert cliente_tributario.llamadas == [venta]
    assert cola_contingencia.guardados == []
    assert factura.identificador_venta == "VENTA-301"
    assert factura.estado == "emitida"


def test_emitir_cuando_falla_la_red_y_no_hay_cola_rechaza_registro_de_pendientes():
    venta = SimpleNamespace(identificador="VENTA-302")

    with pytest.raises(ValueError, match="cola de contingencia"):
        emitir(
            venta,
            detector_conexion=lambda: False,
            cola_contingencia=None,
        )


def test_emitir_cuando_falla_el_servicio_tributario_y_la_cola_no_expone_guardar_rechaza_registro():
    venta = SimpleNamespace(identificador="VENTA-303")

    with pytest.raises(ValueError, match="debe exponer guardar"):
        emitir(
            venta,
            detector_conexion=lambda: True,
            cliente_tributario=lambda venta: (_ for _ in ()).throw(RuntimeError("caida")),
            cola_contingencia=ColaContingenciaSinGuardar(),
        )


def test_sincronizar_pendientes_con_cola_sin_obtener_pendientes_usa_atributo_pendientes_y_elimina_solo_los_exitosos():
    factura_1 = SimpleNamespace(identificador_venta="VENTA-304", estado="contingencia")
    factura_2 = SimpleNamespace(identificador_venta="VENTA-305", estado="contingencia")
    cola_contingencia = ColaContingenciaConPendientes([factura_1, factura_2])
    sincronizador = SincronizadorQueFallaEnLaSegunda()

    procesadas = sincronizar_pendientes(
        cola_contingencia=cola_contingencia,
        sincronizador_azure=sincronizador,
    )

    assert procesadas == 2
    assert sincronizador.llamadas == [factura_1, factura_2]
    assert cola_contingencia.pendientes == [factura_2]
    assert cola_contingencia.guardados == []


def test_sincronizar_pendientes_con_cola_nula_devuelve_cero():
    assert sincronizar_pendientes(cola_contingencia=None, sincronizador_azure=lambda factura: True) == 0
