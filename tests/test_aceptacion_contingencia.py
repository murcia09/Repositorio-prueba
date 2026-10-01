from types import SimpleNamespace

from facturacion.emision import emitir, sincronizar_pendientes


class VerificadorConexionOK:
    def hay_conexion(self):
        return True


class VerificadorConexionFallida:
    def hay_conexion(self):
        return False


class ProcesadorTributarioOK:
    def procesar(self, venta):
        return {
            "factura_id": "F-123456",
            "venta_id": venta["id"],
            "estado": "emitida",
        }


class ProcesadorTributarioFallido:
    def procesar(self, venta):
        raise RuntimeError("servicio tributario no disponible")


class ColaPendientesDoble:
    def __init__(self):
        self.registros = []

    def registrar(self, item):
        self.registros.append(item)


class SincronizadorDoble:
    def __init__(self):
        self.sincronizadas = []

    def sincronizar(self, factura):
        self.sincronizadas.append(factura)
        return True


def test_C1_emitir_con_conectividad_y_servicio_ok_devuelve_factura_emitida_con_id_y_venta():
    venta = {
        "id": "V-1001",
        "total": 125.5,
        "moneda": "USD",
        "items": [
            {"sku": "SKU-001", "cantidad": 1, "precio_unitario": 125.5},
        ],
    }

    resultado = emitir(
        venta,
        verificador_conexion=VerificadorConexionOK(),
        procesador_tributario=ProcesadorTributarioOK(),
        cola_pendientes=ColaPendientesDoble(),
    )

    assert resultado["estado"] == "emitida"
    assert resultado["venta_id"] == "V-1001"
    assert resultado["factura_id"] == "F-123456"


def test_C2_si_falla_la_conexion_la_venta_se_registra_en_cola_y_el_retorno_indica_contingencia():
    venta = {
        "id": "V-2001",
        "total": 80,
        "items": [
            {"sku": "SKU-002", "cantidad": 2, "precio_unitario": 40},
        ],
    }
    cola = ColaPendientesDoble()

    resultado = emitir(
        venta,
        verificador_conexion=VerificadorConexionFallida(),
        procesador_tributario=ProcesadorTributarioOK(),
        cola_pendientes=cola,
    )

    assert len(cola.registros) == 1
    assert cola.registros[0]["venta_id"] == "V-2001"
    assert resultado["estado"] in {"contingencia", "pendiente_sincronizacion", "en_cola"}


def test_C2_si_falla_el_servicio_tributario_la_venta_se_registra_en_cola_y_el_retorno_indica_pendiente():
    venta = {
        "id": "V-2002",
        "total": 90,
        "items": [
            {"sku": "SKU-003", "cantidad": 3, "precio_unitario": 30},
        ],
    }
    cola = ColaPendientesDoble()

    resultado = emitir(
        venta,
        verificador_conexion=VerificadorConexionOK(),
        procesador_tributario=ProcesadorTributarioFallido(),
        cola_pendientes=cola,
    )

    assert len(cola.registros) == 1
    assert cola.registros[0]["venta_id"] == "V-2002"
    assert resultado["estado"] in {"contingencia", "pendiente_sincronizacion", "en_cola"}


def test_C3_sincronizar_pendientes_llama_al_sincronizador_una_vez_por_cada_factura_pendiente():
    pendientes = [
        {"factura_id": "F-1", "venta_id": "V-1"},
        {"factura_id": "F-2", "venta_id": "V-2"},
        {"factura_id": "F-3", "venta_id": "V-3"},
    ]
    sincronizador = SincronizadorDoble()

    resultado = sincronizar_pendientes(pendientes, sincronizador=sincronizador)

    assert sincronizador.sincronizadas == pendientes
    assert resultado["sincronizadas"] == 3


def test_C4_emitir_usa_colaboradores_inyectados_en_lugar_de_acceder_a_servicios_reales():
    venta = {
        "id": "V-3001",
        "total": 50,
        "items": [
            {"sku": "SKU-004", "cantidad": 1, "precio_unitario": 50},
        ],
    }
    cola = ColaPendientesDoble()
    verificador = VerificadorConexionOK()
    procesador = ProcesadorTributarioOK()

    resultado = emitir(
        venta,
        verificador_conexion=verificador,
        procesador_tributario=procesador,
        cola_pendientes=cola,
    )

    assert resultado["venta_id"] == "V-3001"
    assert resultado["factura_id"] == "F-123456"
    assert cola.registros == []
