class ColaContingenciaDobleExitosa:
    def __init__(self):
        self.guardados = []

    def guardar(self, item):
        self.guardados.append(item)


class ServicioTributarioDobleExitoso:
    def emitir(self, venta):
        return {"estado": "emitida", "venta_id": venta["venta_id"]}


class ServicioTributarioDobleFalla:
    def emitir(self, venta):
        raise ConnectionError("sin conexión")


class ColaConPendientes:
    def __init__(self, pendientes):
        self.pendientes = list(pendientes)
        self.limpiada = False

    def obtener_pendientes(self):
        return list(self.pendientes)

    def limpiar(self):
        self.pendientes.clear()
        self.limpiada = True


class AzureDobleExitoso:
    def __init__(self):
        self.enviadas = []

    def enviar(self, factura):
        self.enviadas.append(factura)


from facturacion.emision import emitir, sincronizar_pendientes


def test_C1_si_el_servicio_tributario_responde_emitir_devuelve_factura_emitida_y_no_guarda_en_cola():
    venta = {"venta_id": "V-001"}
    servicio_tributario = ServicioTributarioDobleExitoso()
    cola_contingencia = ColaContingenciaDobleExitosa()

    factura = emitir(
        venta,
        servicio_tributario=servicio_tributario,
        cola_contingencia=cola_contingencia,
    )

    assert factura["estado"] == "emitida"
    assert factura["venta_id"] == "V-001"
    assert cola_contingencia.guardados == []


def test_C2_si_falla_el_servicio_tributario_emitir_devuelve_factura_en_contingencia_y_guarda_la_venta_en_cola():
    venta = {"venta_id": "V-001"}
    servicio_tributario = ServicioTributarioDobleFalla()
    cola_contingencia = ColaContingenciaDobleExitosa()

    factura = emitir(
        venta,
        servicio_tributario=servicio_tributario,
        cola_contingencia=cola_contingencia,
    )

    assert factura["estado"] == "contingencia"
    assert factura["venta_id"] == "V-001"
    assert cola_contingencia.guardados == [venta]


def test_C3_sincronizar_pendientes_envia_cada_factura_a_azure_y_limpia_la_cola():
    cola_contingencia = ColaConPendientes(
        [
            {"venta_id": "V-001", "estado": "contingencia"},
            {"venta_id": "V-002", "estado": "contingencia"},
        ]
    )
    azure = AzureDobleExitoso()

    sincronizadas = sincronizar_pendientes(cola_contingencia, azure=azure)

    assert sincronizadas == 2
    assert azure.enviadas == [
        {"venta_id": "V-001", "estado": "contingencia"},
        {"venta_id": "V-002", "estado": "contingencia"},
    ]
    assert cola_contingencia.pendientes == []
    assert cola_contingencia.limpiada is True
