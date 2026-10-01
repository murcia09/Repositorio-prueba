import pytest

from facturacion.emision import emitir, sincronizar_pendientes


class ServicioTributarioRetornoParcial:
    def emitir(self, venta):
        return {"referencia": "F-123"}


class ServicioTributarioRetornoNoDiccionario:
    def emitir(self, venta):
        return "factura-generada"


class ServicioTributarioFallaConexion:
    def emitir(self, venta):
        raise ConnectionError("sin conexión")


class ColaContingenciaRegistrable:
    def __init__(self):
        self.guardados = []

    def guardar(self, item):
        self.guardados.append(item)


class ColaPendientesVacia:
    def __init__(self):
        self.limpiada = False

    def obtener_pendientes(self):
        return []

    def limpiar(self):
        self.limpiada = True


class ColaPendientesConFacturas:
    def __init__(self, pendientes):
        self._pendientes = list(pendientes)
        self.limpiada = False

    def obtener_pendientes(self):
        return list(self._pendientes)

    def limpiar(self):
        self._pendientes.clear()
        self.limpiada = True


class AzureQueFallaEnLaSegundaFactura:
    def __init__(self):
        self.enviadas = []

    def enviar(self, factura):
        self.enviadas.append(factura)
        if len(self.enviadas) == 2:
            raise TimeoutError("azure no responde")


def test_emitir_completa_campos_faltantes_devueltos_por_el_servicio_tributario():
    factura = emitir(
        {"venta_id": "V-001"},
        servicio_tributario=ServicioTributarioRetornoParcial(),
    )

    assert factura == {"referencia": "F-123", "estado": "emitida", "venta_id": "V-001"}


def test_emitir_convierte_un_retorno_no_diccionario_en_factura_emitida():
    factura = emitir(
        {"venta_id": "V-001"},
        servicio_tributario=ServicioTributarioRetornoNoDiccionario(),
    )

    assert factura == {"estado": "emitida", "venta_id": "V-001"}


def test_emitir_en_contingencia_sin_cola_no_falla_y_devuelve_estado_contingencia():
    factura = emitir(
        {"venta_id": "V-001"},
        servicio_tributario=ServicioTributarioFallaConexion(),
    )

    assert factura == {"estado": "contingencia", "venta_id": "V-001"}


def test_sincronizar_pendientes_con_cola_vacia_devuelve_cero_y_limpia_la_cola():
    cola = ColaPendientesVacia()

    sincronizadas = sincronizar_pendientes(cola, azure=object())

    assert sincronizadas == 0
    assert cola.limpiada is True


def test_sincronizar_pendientes_propagala_falla_de_azure_y_no_limpia_si_falla_a_mitad():
    cola = ColaPendientesConFacturas([
        {"venta_id": "V-001", "estado": "contingencia"},
        {"venta_id": "V-002", "estado": "contingencia"},
        {"venta_id": "V-003", "estado": "contingencia"},
    ])
    azure = AzureQueFallaEnLaSegundaFactura()

    with pytest.raises(TimeoutError, match="azure no responde"):
        sincronizar_pendientes(cola, azure=azure)

    assert azure.enviadas == [
        {"venta_id": "V-001", "estado": "contingencia"},
        {"venta_id": "V-002", "estado": "contingencia"},
    ]
    assert cola.limpiada is False
    assert cola._pendientes == [
        {"venta_id": "V-001", "estado": "contingencia"},
        {"venta_id": "V-002", "estado": "contingencia"},
        {"venta_id": "V-003", "estado": "contingencia"},
    ]
