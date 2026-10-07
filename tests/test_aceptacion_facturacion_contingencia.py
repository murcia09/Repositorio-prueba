from types import SimpleNamespace

from facturacion.emision import emitir, sincronizar_pendientes


class ColaContingenciaStub:
    def __init__(self, pendientes=None):
        self.pendientes = list(pendientes or [])
        self.guardados = []
        self.eliminados = []

    def guardar(self, venta_o_factura_pendiente):
        self.guardados.append(venta_o_factura_pendiente)
        self.pendientes.append(venta_o_factura_pendiente)

    def obtener_pendientes(self):
        return list(self.pendientes)

    def eliminar(self, factura_pendiente):
        self.eliminados.append(factura_pendiente)
        if factura_pendiente in self.pendientes:
            self.pendientes.remove(factura_pendiente)


class ClienteTributarioQueFalla:
    def __init__(self):
        self.llamadas = []

    def __call__(self, venta):
        self.llamadas.append(venta)
        raise RuntimeError("servicio tributario no disponible")


class DetectorConexionSinRed:
    def __init__(self):
        self.llamadas = []

    def __call__(self):
        self.llamadas.append(True)
        return False


class SincronizadorAzureStub:
    def __init__(self):
        self.llamadas = []

    def __call__(self, factura_pendiente):
        self.llamadas.append(factura_pendiente)
        return True


class SincronizadorAzureQueFallaEnLaPrimera:
    def __init__(self):
        self.llamadas = []

    def __call__(self, factura_pendiente):
        self.llamadas.append(factura_pendiente)
        return True


def test_C1_si_falla_la_red_o_el_servicio_tributario_se_guarda_en_cola_y_se_devuelve_factura_en_contingencia():
    venta = SimpleNamespace(identificador="VENTA-200")
    cola_contingencia = ColaContingenciaStub()
    cliente_tributario = ClienteTributarioQueFalla()
    detector_conexion = DetectorConexionSinRed()

    factura = emitir(
        venta,
        cliente_tributario=cliente_tributario,
        detector_conexion=detector_conexion,
        cola_contingencia=cola_contingencia,
    )

    assert cliente_tributario.llamadas == [] or cliente_tributario.llamadas == [venta]
    assert detector_conexion.llamadas == [True]
    assert len(cola_contingencia.guardados) == 1
    assert cola_contingencia.guardados[0] == venta or getattr(cola_contingencia.guardados[0], "identificador_venta", None) == venta.identificador
    assert factura.identificador_venta == venta.identificador
    assert factura.estado in {"pendiente", "contingencia"}


def test_C2_cuando_hay_facturas_pendientes_y_vuelve_la_red_se_intentan_sincronizar_todas_y_se_informa_cuantas():
    factura_1 = SimpleNamespace(identificador_venta="VENTA-201", estado="pendiente")
    factura_2 = SimpleNamespace(identificador_venta="VENTA-202", estado="contingencia")
    cola_contingencia = ColaContingenciaStub([factura_1, factura_2])
    sincronizador_azure = SincronizadorAzureStub()

    procesadas = sincronizar_pendientes(
        cola_contingencia=cola_contingencia,
        sincronizador_azure=sincronizador_azure,
    )

    assert sincronizador_azure.llamadas == [factura_1, factura_2]
    assert procesadas == 2


def test_C3_después_de_sincronizar_correctamente_una_factura_pendiente_ya_no_permanece_en_cola():
    factura_pendiente = SimpleNamespace(identificador_venta="VENTA-203", estado="pendiente")
    cola_contingencia = ColaContingenciaStub([factura_pendiente])
    sincronizador_azure = SincronizadorAzureStub()

    procesadas = sincronizar_pendientes(
        cola_contingencia=cola_contingencia,
        sincronizador_azure=sincronizador_azure,
    )

    assert procesadas == 1
    assert sincronizador_azure.llamadas == [factura_pendiente]
    assert cola_contingencia.pendientes == []
    assert cola_contingencia.eliminados == [factura_pendiente]
